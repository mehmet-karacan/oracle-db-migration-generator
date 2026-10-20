"""SSH identity or HTTPS askpass; secrets never enter a URL, file or argv."""
import os
import shlex
import tempfile
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import urlsplit

from ..config.loader import ConfigError


ASKPASS = '''#!/bin/sh
case "$1" in
    *Username*) printf '%s\\n' "$ODMG_SOURCE_USER" ;;
    *Password*) printf '%s\\n' "$ODMG_SOURCE_PASSWORD" ;;
    *) exit 1 ;;
esac
'''


@contextmanager
def git_read_environment(source: dict, credentials=None):
    parsed = urlsplit(source.get('repository', ''))
    if parsed.scheme not in {'ssh', 'https'} or not parsed.hostname or parsed.password or parsed.query or parsed.fragment:
        raise ConfigError('SOURCE_URL_INVALID')
    env = dict(os.environ, GIT_TERMINAL_PROMPT='0', GIT_OPTIONAL_LOCKS='0')
    if parsed.scheme == 'ssh':
        if parsed.username != 'git':
            raise ConfigError('SOURCE_SSH_USER_INVALID')
        command = 'ssh -o BatchMode=yes -o StrictHostKeyChecking=yes -o ConnectTimeout=8'
        if source.get('ssh_identity_file'):
            identity = Path(source['ssh_identity_file']).resolve()
            if not identity.is_file():
                raise ConfigError('SSH_IDENTITY_FILE_MISSING')
            command += ' -o IdentitiesOnly=yes -i ' + shlex.quote(identity.as_posix())
        env['GIT_SSH_COMMAND'] = command
        yield env
    else:
        if parsed.username or not credentials or not source.get('credential_id'):
            raise ConfigError('SOURCE_HTTPS_CREDENTIAL_RESOLVER_REQUIRED')
        credential = credentials(source['credential_id'])
        with tempfile.TemporaryDirectory(prefix='odmg-askpass-') as directory:
            askpass = Path(directory) / 'askpass.sh'
            askpass.write_text(ASKPASS, encoding='utf-8', newline='\n')
            askpass.chmod(0o700)
            env.update(GIT_ASKPASS=str(askpass), ODMG_SOURCE_USER=credential.username,
                       ODMG_SOURCE_PASSWORD=credential.password)
            # Disable credential helpers and redirects for this child process only.
            # Do not modify a user's repository/global Git configuration.
            env.update(GIT_CONFIG_COUNT='3', GIT_CONFIG_KEY_0='credential.helper', GIT_CONFIG_VALUE_0='',
                       GIT_CONFIG_KEY_1='http.followRedirects', GIT_CONFIG_VALUE_1='false',
                       GIT_CONFIG_KEY_2='http.sslVerify', GIT_CONFIG_VALUE_2='true')
            yield env
