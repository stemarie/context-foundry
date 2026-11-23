"""Disposable actual-image AI.Contract fixture. Never opens SQLite or uses an existing root."""
import json
import os
from pathlib import Path
import socket
import shlex
import subprocess
import time
import urllib.request
import uuid

from foundry_runtime import constants as settings
from foundry_runtime.core import Barrier


class DockerService:
    def __init__(self, host, image, root):
        self.host, self.root = host, Path(root)
        self.name = 'cf-native-' + uuid.uuid4().hex[:12]
        self.volume = self.name + '-state'
        self.label = 'context-foundry.proof=' + self.name
        self.tokens, self.current, self.generation = {}, None, 0
        self.events = []
        info = json.loads(self.docker('image', 'inspect', image))[0]
        if info['Config']['User'] != settings.FIXTURE_CONTAINER_UID:
            raise Barrier('actual service proof requires the existing non-root image')
        self.image = info['Id']
        self.docker('volume', 'create', '--label', self.label, self.volume)
        self.mount = 'type=volume,src=' + self.volume + ',dst=' + settings.FIXTURE_STATE_DIRECTORY
        self.docker('run', '--rm', '--label', self.label, '--mount', self.mount, settings.FIXTURE_HELPER_IMAGE,
                    'sh', '-c', f'chown {shlex.quote(settings.FIXTURE_CONTAINER_USER)} {shlex.quote(settings.FIXTURE_STATE_DIRECTORY)} && chmod {settings.PRIVATE_DIRECTORY_MODE:o} {shlex.quote(settings.FIXTURE_STATE_DIRECTORY)}')
        with socket.socket() as listener:
            listener.bind((settings.LOCAL_BIND_HOST, 0)); self.port = listener.getsockname()[1]
        self.url = f'http://{settings.LOCAL_BIND_HOST}:{self.port}'
        for role, scope in [('admin','admin'),('architect','read,write,architect'),('reader','read')]:
            self.tokens[role] = self.issue_token('mock-' + role, scope)

    def docker(self, *args):
        result = subprocess.run(['docker', '--host', self.host, *args], capture_output=True, text=True, timeout=settings.FIXTURE_DOCKER_TIMEOUT_SECONDS)
        if result.returncode:
            raise Barrier('owned Docker fixture operation failed')
        return ((result.stdout + result.stderr) if args[0]=='logs' else result.stdout).strip()

    def issue_token(self, actor, scopes):
        result = self.docker('run','--rm','--label',self.label,'--user',settings.FIXTURE_CONTAINER_USER,
                             '--mount',self.mount,self.image,'token','issue',actor,scopes)
        return next(line[6:] for line in result.splitlines() if line.startswith('token='))

    def start(self):
        self.generation += 1
        self.current = self.name + '-' + str(self.generation)
        container = self.docker('run','-d','--name',self.current,'--label',self.label,'--user',settings.FIXTURE_CONTAINER_USER,
            '--mount',self.mount,'-p',f'{settings.LOCAL_BIND_HOST}:{self.port}:{settings.FIXTURE_CONTAINER_PORT}',self.image)
        deadline = time.monotonic()+settings.FIXTURE_READY_TIMEOUT_SECONDS
        while time.monotonic()<deadline:
            try:
                with urllib.request.urlopen(self.url+'/readyz',timeout=settings.FIXTURE_READY_REQUEST_TIMEOUT_SECONDS) as response:
                    if response.status==200:break
            except OSError:time.sleep(settings.FIXTURE_POLL_INTERVAL_SECONDS)
        else:raise Barrier('owned Docker service not ready')
        actual=json.loads(self.docker('inspect',self.current))[0]
        if actual['Image'] != self.image or actual['Config']['User'] != settings.FIXTURE_CONTAINER_USER:
            raise Barrier('service image/identity changed')
        self.events.append({'container':container,'image':self.image,'generation':self.generation,
                            'user':actual['Config']['User'],'origin':self.url})
        return self.url

    def stop(self):
        if self.current:
            logs=self.docker('logs',self.current)
            if any(token in logs for token in self.tokens.values()):
                raise Barrier('fixture log contains a credential')
            self.docker('rm','-f',self.current);self.current=None

    def replace(self, downtime=settings.FIXTURE_REPLACEMENT_DOWNTIME_SECONDS):
        before=self.events[-1]
        self.stop()
        time.sleep(downtime)  # Bounded deliberate local outage; no production networking affected.
        self.start()
        after=self.events[-1]
        if before['container']==after['container'] or before['image']!=after['image']:
            raise Barrier('container replacement identity proof failed')
        return {'before':before,'after':after,'downtime_seconds':downtime,'same_volume':self.volume}

    def cleanup(self):
        self.stop()
        self.docker('volume','rm',self.volume)
        if self.docker('ps','-aq','--filter','label='+self.label):
            raise Barrier('owned fixture container remains')
