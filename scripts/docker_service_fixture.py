"""Disposable actual-image AI.Contract fixture. Never opens SQLite or uses an existing root."""
import json
import os
from pathlib import Path
import socket
import subprocess
import time
import urllib.request
import uuid

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
        if info['Config']['User'] != '65532':
            raise Barrier('actual service proof requires the existing non-root image')
        self.image = info['Id']
        self.docker('volume', 'create', '--label', self.label, self.volume)
        self.mount = 'type=volume,src=' + self.volume + ',dst=/var/lib/ai-contract'
        self.docker('run', '--rm', '--label', self.label, '--mount', self.mount, 'busybox:1.36',
                    'sh', '-c', 'chown 65532:65532 /var/lib/ai-contract && chmod 700 /var/lib/ai-contract')
        with socket.socket() as listener:
            listener.bind(('127.0.0.1', 0)); self.port = listener.getsockname()[1]
        self.url = 'http://127.0.0.1:' + str(self.port)
        for role, scope in [('admin','admin'),('architect','read,write,architect'),('reader','read')]:
            self.tokens[role] = self.issue_token('mock-' + role, scope)

    def docker(self, *args):
        result = subprocess.run(['docker', '--host', self.host, *args], capture_output=True, text=True, timeout=120)
        if result.returncode:
            raise Barrier('owned Docker fixture operation failed')
        return ((result.stdout + result.stderr) if args[0]=='logs' else result.stdout).strip()

    def issue_token(self, actor, scopes):
        result = self.docker('run','--rm','--label',self.label,'--user','65532:65532',
                             '--mount',self.mount,self.image,'token','issue',actor,scopes)
        return next(line[6:] for line in result.splitlines() if line.startswith('token='))

    def start(self):
        self.generation += 1
        self.current = self.name + '-' + str(self.generation)
        container = self.docker('run','-d','--name',self.current,'--label',self.label,'--user','65532:65532',
            '--mount',self.mount,'-p','127.0.0.1:'+str(self.port)+':8080',self.image)
        deadline = time.monotonic()+30
        while time.monotonic()<deadline:
            try:
                with urllib.request.urlopen(self.url+'/readyz',timeout=1) as response:
                    if response.status==200:break
            except OSError:time.sleep(.2)
        else:raise Barrier('owned Docker service not ready')
        actual=json.loads(self.docker('inspect',self.current))[0]
        if actual['Image'] != self.image or actual['Config']['User'] != '65532:65532':
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

    def replace(self, downtime=6):
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
