import yaml
from github import Repository

def get_enable_plugin(repo_client: Repository.Repository) -> list:
    try:
        file = repo_client.get_contents(".github/gitautomator.yaml")
        config = yaml.safe_load(file.decoded_content.decode())
        return config['plugins']
    except Exception as _:
        return []

def expand_aliases(owners_list, aliases_map):
    """
    Expands any aliases found in the owners_list using the provided aliases_map.
    If the item exists in aliases_map and is a list, its users are added;
    otherwise, the item is added as is.
    """
    expanded = set()
    for item in owners_list:
        if item in aliases_map and isinstance(aliases_map[item], list):
            expanded.update(aliases_map[item])
        else:
            expanded.add(item)
    return expanded

def get_owners(repo_client: Repository.Repository) -> list:
    """
    Combines owners from three sources:
      1. .github/gitautomator.yaml (expects an 'owners' key with a list of usernames)
      2. OWNERS_ALIASES (mapping from an alias to a list of real user names)
      3. OWNERS (expected to contain 'approvers' and/or 'reviewers' as lists)

    Returns a merged list of owner usernames.
    """
    owners_set = set()
    aliases_map = {}

    # 1. Read .github/gitautomator.yaml for "owners"
    try:
        file = repo_client.get_contents(".github/gitautomator.yaml")
        config = yaml.safe_load(file.decoded_content.decode())
        if config and 'owners' in config and isinstance(config['owners'], list):
            owners_set.update(config['owners'])
    except Exception as _:
        pass

    # 2. Read OWNERS_ALIASES for alias mapping
    try:
        file = repo_client.get_contents("OWNERS_ALIASES")
        alias_data = yaml.safe_load(file.decoded_content.decode())
        if isinstance(alias_data, dict):
            if "aliases" in alias_data and isinstance(alias_data["aliases"], dict):
                aliases_map = alias_data["aliases"]
            else:
                aliases_map = alias_data
    except Exception as _:
        pass

    # 3. Read OWNERS and expand the "approvers" and "reviewers" fields using aliases_map
    try:
        file = repo_client.get_contents("OWNERS")
        owners_data = yaml.safe_load(file.decoded_content.decode())
        if isinstance(owners_data, dict):
            approvers = owners_data.get("approvers", [])
            reviewers = owners_data.get("reviewers", [])
            owners_set.update(expand_aliases(approvers, aliases_map))
            owners_set.update(expand_aliases(reviewers, aliases_map))
    except Exception as _:
        pass

    return list(owners_set)
