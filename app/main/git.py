def get_file_sha(repo, path, branch):
    try:
        contents = repo.get_contents(path, ref=branch)
        return contents.sha
    except:
        return None

def get_branch_sha(repo, branch):
    try:
        ref = repo.get_git_ref(f'heads/{branch}')
        return ref.object.sha
    except:
        return None
    
def create_branch(repo, branch, source_branch="master"):
    source_branch_sha = get_branch_sha(repo, source_branch)
    if not source_branch_sha:
        raise ValueError(f"Source branch '{source_branch}' does not exist.")
    
    try:
        repo.create_git_ref(ref=f'refs/heads/{branch}', sha=source_branch_sha)
        print(f"Branch '{branch}' created successfully.")
    except Exception as e:
        print(f"Failed to create branch '{branch}': {e}")

def create_pull_request(repo, branch, base="master", title="New changes", body="Please review these changes."):
    try:
        pr = repo.create_pull(title=title, body=body, head=branch, base=base)
        print(f"Pull request created: {pr.html_url}")
    except Exception as e:
        print(f"Failed to create pull request: {e}")