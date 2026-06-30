import os
import requests
from typing import List, Dict, Optional


class GitHubService:

    BASE_URL = 'https://api.github.com'

    def __init__(self, token: str = None):
        self.token = token or os.environ.get('GITHUB_TOKEN', '')
        self.headers = {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'AI-Code-Review-Assistant'
        }

    def _get(self, endpoint: str, params: dict = None) -> Optional[dict]:
        try:
            url = f'{self.BASE_URL}{endpoint}'
            response = requests.get(url, headers=self.headers, params=params, timeout=15)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f'GitHub API error: {str(e)}')

    def get_user_repos(self, username: str = None) -> List[Dict]:
        if username:
            data = self._get(f'/users/{username}/repos', params={'per_page': 50, 'sort': 'updated'})
        else:
            data = self._get('/user/repos', params={'per_page': 50, 'sort': 'updated', 'visibility': 'all'})

        return [{
            'name': repo['name'],
            'full_name': repo['full_name'],
            'url': repo['html_url'],
            'clone_url': repo['clone_url'],
            'description': repo.get('description', ''),
            'language': repo.get('language', 'Unknown'),
            'stars': repo.get('stargazers_count', 0),
            'forks': repo.get('forks_count', 0),
            'is_private': repo.get('private', False),
            'default_branch': repo.get('default_branch', 'main'),
            'updated_at': repo.get('updated_at', '')
        } for repo in (data or [])]

    def get_file_content(self, repo_full_name: str, file_path: str, branch: str = 'main') -> str:
        endpoint = f'/repos/{repo_full_name}/contents/{file_path}'
        data = self._get(endpoint, params={'ref': branch})
        if data and data.get('encoding') == 'base64':
            import base64
            return base64.b64decode(data['content']).decode('utf-8')
        return ''

    def get_pull_requests(self, repo_full_name: str) -> List[Dict]:
        data = self._get(f'/repos/{repo_full_name}/pulls', params={'state': 'open', 'per_page': 20})
        return [{
            'number': pr['number'],
            'title': pr['title'],
            'author': pr['user']['login'],
            'url': pr['html_url'],
            'created_at': pr['created_at'],
            'base_branch': pr['base']['ref'],
            'head_branch': pr['head']['ref'],
            'changed_files': pr.get('changed_files', 0),
            'additions': pr.get('additions', 0),
            'deletions': pr.get('deletions', 0),
        } for pr in (data or [])]

    def get_pr_files(self, repo_full_name: str, pr_number: int) -> List[Dict]:
        data = self._get(f'/repos/{repo_full_name}/pulls/{pr_number}/files')
        return [{
            'filename': f['filename'],
            'status': f['status'],
            'additions': f.get('additions', 0),
            'deletions': f.get('deletions', 0),
            'patch': f.get('patch', ''),
        } for f in (data or [])]

    def get_repo_tree(self, repo_full_name: str, branch: str = 'main') -> List[str]:
        data = self._get(f'/repos/{repo_full_name}/git/trees/{branch}', params={'recursive': '1'})
        if data and 'tree' in data:
            return [item['path'] for item in data['tree'] if item['type'] == 'blob']
        return []

    def create_pr_comment(self, repo_full_name: str, pr_number: int, comment: str) -> bool:
        url = f'{self.BASE_URL}/repos/{repo_full_name}/issues/{pr_number}/comments'
        try:
            response = requests.post(
                url,
                headers=self.headers,
                json={'body': comment},
                timeout=15
            )
            return response.status_code == 201
        except Exception:
            return False

    def get_authenticated_user(self) -> Optional[Dict]:
        data = self._get('/user')
        if data:
            return {
                'username': data['login'],
                'name': data.get('name', ''),
                'avatar_url': data.get('avatar_url', ''),
                'email': data.get('email', ''),
                'public_repos': data.get('public_repos', 0),
                'followers': data.get('followers', 0),
            }
        return None

    def validate_token(self) -> bool:
        try:
            user = self.get_authenticated_user()
            return user is not None
        except Exception:
            return False
