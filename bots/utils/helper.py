import yaml

from github import Repository

def get_owners(repo_client : Repository.Repository) -> list:
    try:
        file = repo_client.get_contents(".github/gitautomator.yaml")
        config = yaml.safe_load(file.decoded_content.decode())
        return config['owners']
    except Exception as _:
        return []

def get_enable_plugin(repo_client: Repository.Repository) -> list:
    try:
        file = repo_client.get_contents(".github/gitautomator.yaml")
        config = yaml.safe_load(file.decoded_content.decode())
        return config['plugins']
    except Exception as _:
        return []
