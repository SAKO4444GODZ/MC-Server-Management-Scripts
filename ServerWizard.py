import os
import requests
import shutil
import json
import sys
import subprocess
from typing import Dict, Optional

class ServerWizard:
    """
    A comprehensive tool for automating Minecraft server setup across different server types.
    """
    
    # Server type configurations
    SERVER_TYPES = {
        'vanilla': {
            'base_url': 'https://piston-data.mojang.com/v1/objects/{}/server.jar',
            'version_manifest_url': 'https://piston-meta.mojang.com/mc/game/version_manifest.json'
        },
        'paper': {
            'base_url': 'https://papermc.io/api/v2/projects/paper/versions/{}/builds/{}/downloads/{}',
            'api_url': 'https://papermc.io/api/v2/projects/paper/versions/{}'
        },
        'forge': {
            'base_url': 'https://maven.minecraftforge.net/net/minecraftforge/forge/{}/forge-{}-installer.jar',
            'version_url': 'https://files.minecraftforge.net/net/minecraftforge/forge/'
        },
        'fabric': {
            'base_url': 'https://meta.fabricmc.net/v2/versions/loader/{}/{}/server/jar'
        }
    }
    
    def __init__(self, server_type: str = 'vanilla', version: Optional[str] = None):
        """
        Initialize ServerWizard with specified server type and version.
        
        :param server_type: Type of Minecraft server (vanilla, paper, forge, fabric)
        :param version: Specific Minecraft version to install
        """
        self.server_type = server_type.lower()
        self.version = version
        self.server_dir = None
        
        if self.server_type not in self.SERVER_TYPES:
            raise ValueError(f"Unsupported server type: {server_type}")
    
    def _create_server_directory(self):
        """
        Create a structured server directory with necessary subdirectories.
        """
        base_dir = os.path.join(os.getcwd(), f"minecraft_{self.server_type}_server")
        os.makedirs(base_dir, exist_ok=True)
        
        # Create standard Minecraft server subdirectories
        subdirs = ['world', 'plugins', 'mods', 'config', 'logs']
        for subdir in subdirs:
            os.makedirs(os.path.join(base_dir, subdir), exist_ok=True)
        
        self.server_dir = base_dir
        return base_dir
    
    def _fetch_latest_vanilla_version(self) -> str:
        """
        Fetch the latest Minecraft vanilla version.
        
        :return: Latest Minecraft version
        """
        try:
            response = requests.get(self.SERVER_TYPES['vanilla']['version_manifest_url'])
            versions = response.json()
            latest_version = versions['latest']['release']
            return latest_version
        except Exception as e:
            print(f"Error fetching version: {e}")
            return None
    
    def _download_server_jar(self):
        """
        Download server JAR based on server type and version.
        """
        if not self.version:
            if self.server_type == 'vanilla':
                self.version = self._fetch_latest_vanilla_version()
            else:
                raise ValueError("Version must be specified for this server type.")
        
        jar_path = os.path.join(self.server_dir, 'server.jar')
        
        if self.server_type == 'vanilla':
            version_data = requests.get(f'https://launchermeta.mojang.com/mc/game/version_manifest.json').json()
            for version in version_data['versions']:
                if version['id'] == self.version:
                    version_url = version['url']
                    version_details = requests.get(version_url).json()
                    download_url = version_details['downloads']['server']['url']
                    break
            
            response = requests.get(download_url)
        elif self.server_type == 'paper':
            # Fetch latest build for specified version
            version_api = self.SERVER_TYPES['paper']['api_url'].format(self.version)
            builds_response = requests.get(version_api)
            latest_build = builds_response.json()['builds'][-1]
            
            download_url = self.SERVER_TYPES['paper']['base_url'].format(
                self.version, latest_build, 
                f'paper-{self.version}-{latest_build}.jar'
            )
            response = requests.get(download_url)
        
        # Download the JAR
        with open(jar_path, 'wb') as f:
            f.write(response.content)
        
        return jar_path
    
    def _create_eula_file(self):
        """
        Create EULA file and prompt user for acceptance.
        """
        eula_path = os.path.join(self.server_dir, 'eula.txt')
        
        print("\n--- Minecraft EULA ---")
        print("To run this server, you must agree to Minecraft's EULA.")
        print("https://account.mojang.com/documents/minecraft_eula")
        
        while True:
            response = input("Do you agree to the EULA? (yes/no): ").lower()
            if response == 'yes':
                with open(eula_path, 'w') as f:
                    f.write('eula=true')
                print("EULA accepted.")
                break
            elif response == 'no':
                print("You must accept the EULA to run the server.")
                sys.exit(1)
    
    def _create_server_properties(self):
        """
        Create default server.properties file.
        """
        properties_path = os.path.join(self.server_dir, 'server.properties')
        default_properties = {
            'difficulty': 'normal',
            'gamemode': 'survival',
            'max-players': '20',
            'online-mode': 'true',
            'pvp': 'true'
        }
        
        with open(properties_path, 'w') as f:
            for key, value in default_properties.items():
                f.write(f"{key}={value}\n")
    
    def setup_server(self):
        """
        Main method to set up the Minecraft server.
        """
        print(f"Setting up {self.server_type.capitalize()} Minecraft Server")
        print(f"Version: {self.version or 'Latest'}")
        
        # Create server directory
        self._create_server_directory()
        
        # Download server JAR
        jar_path = self._download_server_jar()
        print(f"Server JAR downloaded: {jar_path}")
        
        # Create EULA file
        self._create_eula_file()
        
        # Create server properties
        self._create_server_properties()
        
        # Create start script
        self._create_start_script()
        
        print("\n--- Server Setup Complete ---")
        print(f"Server located at: {self.server_dir}")
        print("Run the start script to launch your server.")
    
    def _create_start_script(self):
        """
        Create a cross-platform start script for the server.
        """
        # Windows batch script
        with open(os.path.join(self.server_dir, 'start.bat'), 'w') as f:
            f.write('@echo off\n')
            f.write('java -Xmx2G -Xms1G -jar server.jar nogui\n')
            f.write('pause\n')
        
        # Unix/Linux shell script
        with open(os.path.join(self.server_dir, 'start.sh'), 'w') as f:
            f.write('#!/bin/bash\n')
            f.write('java -Xmx2G -Xms1G -jar server.jar nogui\n')
        
        # Make shell script executable
        os.chmod(os.path.join(self.server_dir, 'start.sh'), 0o755)

def main():
    print("--- Minecraft Server Wizard ---")
    
    # Prompt for server type
    print("Available Server Types:")
    print("1. Vanilla")
    print("2. Paper")
    print("3. Forge")
    print("4. Fabric")
    
    type_map = {
        '1': 'vanilla',
        '2': 'paper',
        '3': 'forge',
        '4': 'fabric'
    }
    
    while True:
        server_type_choice = input("Select server type (1-4): ")
        if server_type_choice in type_map:
            server_type = type_map[server_type_choice]
            break
        print("Invalid selection. Please choose 1-4.")
    
    # Prompt for version
    version = input("Enter Minecraft version (leave blank for latest): ").strip() or None
    
    # Create and setup server
    wizard = ServerWizard(server_type=server_type, version=version)
    wizard.setup_server()

if __name__ == "__main__":
    main()
