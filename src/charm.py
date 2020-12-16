#!/usr/bin/env python3
# Copyright 2020 Jonatas Baldin
# See LICENSE file for licensing details.

import logging
from pathlib import Path
import yaml

from ops.charm import CharmBase
from ops.main import main
from ops.framework import StoredState
from ops.model import ActiveStatus

logger = logging.getLogger(__name__)


class ExternalSecretsCharm(CharmBase):
    _stored = StoredState()

    def __init__(self, *args):
        super().__init__(*args)
        self.framework.observe(self.on.config_changed, self._on_config_changed)

    def _on_config_changed(self, _):
        logger.info("entering _on_config_changed")

        pod_spec = self._build_pod_spec()
        self.model.pod.set_spec(pod_spec)
        self.unit.status = ActiveStatus(f'{self.app.name} pod ready')

    def _build_crds(self):
        crds = []
        try:
            crds = [
                yaml.load(Path(f).read_text(), Loader=yaml.FullLoader)
                for f in [
                    'files/external_secret_crd.yaml',
                    'files/secret_store_crd.yaml',
                ]
            ]
        except yaml.YAMLError as e:
            logger.error('could not read yaml file', e)
            return

        return crds

    def _build_rules(self):
        rules = {}
        try:
            rules = yaml.load(open(Path('files/rbac.yaml'), 'r'), Loader=yaml.FullLoader)
        except yaml.YAMLError as e:
            logger.error('could not read yaml file', e)
            return

        return rules

    def _build_pod_spec(self):
        crds = self._build_crds()
        rules = self._build_rules()

        custom_resource_definitions = [
            {
                'name': crd.get('metadata').get('name'),
                'spec': crd.get('spec'),
            } for crd in crds
        ]

        spec = {
            'version': 3,
            'kubernetesResources': {
                'customResourceDefinitions': custom_resource_definitions,
            },
            'serviceAccount': {
                'roles': [{
                    'global': True,
                    'rules': rules.get('rules'),
                }],
            },
            'containers': [
                {
                    'name': self.app.name,
                    'imageDetails': {'imagePath': 'containersol/externalsecret-operator:master'},
                    'ports': [{'containerPort': 8080, 'protocol': 'TCP', 'name': 'operator'}],
                    'command': ['/manager', '--enable-leader-election']
                }
            ]
        }

        return spec


if __name__ == '__main__':
    main(ExternalSecretsCharm)
