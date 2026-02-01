from github import Github, GithubException
import os
import logging

logger = logging.getLogger(__name__)

class GitHubClient:
    def __init__(self, token, repo_name):
        self.g = Github(token)
        self.repo_name = repo_name
        try:
            self.repo = self.g.get_repo(repo_name)
        except Exception as e:
            logger.error(f"Failed to access repository {repo_name}: {e}")
            self.repo = None

    def get_or_create_release(self, tag_name="downloads"):
        """
        Gets an existing release by tag or creates a new one.
        We use a single release to store all audio files to keep it simple,
        or we could create releases per date.
        For this project, a single rolling release 'downloads' is a good start.
        """
        if not self.repo:
            return None

        try:
            release = self.repo.get_release(tag_name)
            return release
        except GithubException:
            logger.info(f"Release {tag_name} not found, creating it...")
            try:
                # Create the release
                release = self.repo.create_git_release(
                    tag=tag_name,
                    name="Audio Downloads",
                    message="Automated audio downloads from YouTube",
                    draft=False,
                    prerelease=False
                )
                return release
            except Exception as e:
                logger.error(f"Failed to create release: {e}")
                return None

    def upload_asset(self, release, file_path, label=None):
        """
        Uploads a file to a specific release.
        """
        if not release:
            return None

        file_name = os.path.basename(file_path)
        try:
            # Check if asset already exists
            for asset in release.get_assets():
                if asset.name == file_name:
                    logger.info(f"Asset {file_name} already exists. Skipping upload.")
                    return asset.browser_download_url

            logger.info(f"Uploading {file_name}...")
            asset = release.upload_asset(file_path, label=label or file_name)
            return asset.browser_download_url
        except Exception as e:
            logger.error(f"Failed to upload asset {file_name}: {e}")
            return None

    def delete_asset(self, release, file_name):
        """
        Deletes a specific asset from a release.
        """
        if not release:
            return False

        try:
            for asset in release.get_assets():
                if asset.name == file_name:
                    logger.info(f"Deleting old asset {file_name}...")
                    asset.delete_asset()
                    return True
            return False # Asset not found
        except Exception as e:
            logger.error(f"Failed to delete asset {file_name}: {e}")
            return False

    def list_assets(self, release):
        """
        Returns a list of asset names in the release.
        """
        if not release:
            return []
        return [asset.name for asset in release.get_assets()]
