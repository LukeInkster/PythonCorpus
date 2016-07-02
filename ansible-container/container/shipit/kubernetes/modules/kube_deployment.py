#!/usr/bin/python
#
# Copyright 2016 Ansible by Red Hat
#
# This file is part of ansible-container
#

DOCUMENTATION = '''

module: kube_deployment

short_description: Start, cancel or retry a deployment on a Kubernetes cluster.

description:
  - Start, cancel or retry a deployment on a Kubernetes cluster by setting the C(state) to I(present) or
    I(absent).
  - Supports check mode. Use check mode to view a list of actions the module will take.

options:

'''

EXAMPLES = '''
'''

RETURN = '''
'''
import logging
import logging.config

from ansible.module_utils.basic import *

logger = logging.getLogger('kube_deployment')

LOGGING = (
    {
        'version': 1,
        'disable_existing_loggers': True,
        'handlers': {
            'null': {
                'level': 'DEBUG',
                'class': 'logging.NullHandler',
            },
            'file': {
                'level': 'DEBUG',
                'class': 'logging.FileHandler',
                'filename': 'ansible-container.log'
            }
        },
        'loggers': {
            'kube_deployment': {
                'handlers': ['file'],
                'level': 'INFO',
            },
            'container': {
                'handlers': ['file'],
                'level': 'INFO',
            },
            'compose': {
                'handlers': [],
                'level': 'INFO'
            },
            'docker': {
                'handlers': [],
                'level': 'INFO'
            }
        },
    }
)


class DeploymentManager(object):

    def __init__(self):

        self.arg_spec = dict(
            state=dict(type='str', choices=['present', 'absent'], default='present'),
            labels=dict(type='dict'),
            deployment_name=dict(type='str'),
            recreate=dict(type='bool', default=False),
            replace=dict(type='bool', default=True),
            replicas=dict(type='int', default=1),
            containers=dict(type='list'),
            strategy=dict(type='str', default='RollingUpdate', choices=['Recreate', 'RollingUpdate']),
            volumes=dict(type='list'),
        )

        self.module = AnsibleModule(self.arg_spec,
                                    supports_check_mode=True)

        self.state = None
        self.labels = None
        self.ports = None
        self.deployment_name = None
        self.replace = None
        self.replicas = None
        self.containers = None
        self.strategy = None
        self.recreate = None
        self.volumes = None
        self.api = None
        self.debug = self.module._debug
        self.check_mode = self.module.check_mode

    def exec_module(self):

        for key in self.arg_spec:
            setattr(self, key, self.module.params.get(key))

        if self.debug:
            LOGGING['loggers']['container']['level'] = 'DEBUG'
            LOGGING['loggers']['kube_deployment']['level'] = 'DEBUG'
        logging.config.dictConfig(LOGGING)

        self.api = KubeAPI(self.module)

        actions = []
        changed = False
        deployments = dict()
        results = dict()
        project_switch = None

        if self.state in 'present':
            deployment = self.api.get_resource('deployment', self.deployment_name)
            if not deployment:
                template = self._create_template()
                changed = True
                actions.append("Create deployment %s" % self.deployment_name)
                if not self.check_mode:
                    self.api.create_from_template(template=template)
            elif deployment and self.recreate:
                actions.append("Delete deployment %s" % self.deployment_name)
                changed = True
                template = self._create_template()
                if not self.check_mode:
                    self.api.delete_resource('deployment', self.deployment_name)
                    self.api.create_from_template(template=template)
            elif deployment and self.replace:
                template = self._create_template()
                changed = True
                actions.append("Update deployment %s" % self.deployment_name)
                if not self.check_mode:
                    self.api.replace_from_template(template=template)

            deployments[self.deployment_name.replace('-', '_') + '_deployment'] = \
                self.api.get_resource('deployment', self.deployment_name)

        elif self.state == 'absent':
            if self.api.get_resource('deployment', self.deployment_name):
                changed = True
                actions.append("Delete deployment %s" % self.deployment_name)
                if not self.check_mode:
                    self.api.delete_resource('deployment', self.deployment_name)

        results['changed'] = changed

        if self.check_mode:
            results['actions'] = actions

        if deployments:
            results['ansible_facts'] = deployments

        self.module.exit_json(**results)

    def _create_template(self):

        for container in self.containers:
            if container.get('env'):
                container['env'] = self._env_to_list(container['env'])
            if container.get('ports'):
                container['ports'] = self._port_to_container_ports(container['ports'])

        template = dict(
            apiVersion="extensions/v1beta1",
            kind="Deployment",
            metadata=dict(
                name=self.deployment_name,
            ),
            spec=dict(
                template=dict(
                    metadata=dict(),
                    spec=dict(
                        containers=self.containers,
                    )
                ),
                replicas=self.replicas,
                strategy=dict(
                    type=self.strategy,
                ),
            )
        )

        if self.volumes:
            template['spec']['template']['spec']['volumes'] = self.volumes

        if self.labels:
            template['metadata']['labels'] = self.labels
            template['spec']['template']['metadata']['labels'] = self.labels

        return template

    def _env_to_list(self, env_variables):
        result = []
        for name, value in env_variables.items():
            result.append(dict(
                name=name,
                value=value
            ))
        return result

    @staticmethod
    def _port_to_container_ports(ports):
        result = []
        for port in ports:
            result.append(dict(containerPort=port))
        return result


#The following will be included by `ansble-container shipit` when cloud modules are copied into the role library path.
#include--> kube_api.py


def main():
    manager = DeploymentManager()
    manager.exec_module()

if __name__ == '__main__':
    main()
