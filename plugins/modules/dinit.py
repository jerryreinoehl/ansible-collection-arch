#!/usr/bin/python


from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r"""
---
module: dinit

short_description: Manage dinit services.

version_added: "1.0.0"

description:
    - Controls services on target hosts that use the dinit init system.

options:
    name:
        required: true
        description:
            - Name of the service.
        type: str
        aliases: ["service"]

    state:
        description:
            - C(started)/C(stopped) are idempotent actions that will not run
              commands unless necessary.
        type: str
        choices: ["started", "stopped", "restarted", "reloaded"]

    enabled:
        type: bool
        description:
            - Whether the service should start on boot. B(At least one of
              state and enabled are required.)

extends_documentation_fragment:
    - jerryreinoehl.arch

author:
    - Jerry Reinoehl (@jerryreinoehl)
"""

EXAMPLES = r"""
# Start a service
- name: Start sshd
  jerryreinoehl.arch.dinit:
    name: sshd
    state: started

# Stop a service
- name: Stop sshd
  jerryreinoehl.arch.dinit:
    name: sshd
    state: stopped

# Restart a service
- name: Restart sshd
  jerryreinoehl.arch.dinit:
    name: sshd
    state: restarted

# Reload a service
- name: Reload sshd
  jerryreinoehl.arch.dinit:
    name: sshd
    state: reloaded

# Enable a service
- name: Enable chronyd
  jerryreinoehl.arch.dinit:
    name: chronyd
    enabled: yes

# Start and enable a service
- name: Start and enable chronyd
  jerryreinoehl.arch.dinit:
    name: chronyd
    state: started
    enabled: yes
"""

RETURN = r"""
name:
    description: The original name param that was passed in.
    type: str
    returned: always
    sample: "chronyd"

enabled:
    description: The original enabled param that was passed in.
    type: bool
    returned: always
    sample: True

state:
    description: The original state param that was passed in.
    type: str
    returned: always
    sample: "started"
"""


import os.path

from ansible.module_utils.basic import AnsibleModule


class DinitModule():
    def __init__(self):
        self.module = AnsibleModule(
            argument_spec=dict(
                name=dict(required=True, type="str", aliases=["service"]),
                state=dict(
                    type="str",
                    choices=["started", "stopped", "restarted", "reloaded"],
                ),
                enabled=dict(type="bool"),
            ),
            required_one_of=[["state", "enabled"]],
            supports_check_mode=True,
        )

        self.result = dict(
            name=self.module.params["name"],
            state=self.module.params["state"],
            enabled=self.module.params["enabled"],
            changed=False
        )

        if self.module.check_mode:
            self.module.exit_json(**result)

        self.dinitctl = self.module.get_bin_path("dinitctl", True)
        self.service = self.module.params["name"]

    def run(self):
        if self.module.params["enabled"] == True:
            self.enable_service(self.service)
        elif self.module.params["enabled"] == False:
            self.disable_service(self.service)

        if self.module.params["state"]:
            self.set_service_state(self.service, self.module.params["state"])

        self.module.exit_json(**self.result)

    def is_service_enabled(self, service):
        return os.path.exists(f"/etc/dinit.d/boot.d/{service}")

    def enable_service(self, service):
        if not self.is_service_enabled(service):
            rc, out, err = self.module.run_command(
                f"{self.dinitctl} enable {service}",
                check_rc = True
            )
            self.result["changed"] = True

    def disable_service(self, service):
        if self.is_service_enabled(service):
            rc, out, err = self.module.run_command(
                f"{self.dinitctl} disable {service}",
                check_rc = True
            )
            self.result["changed"] = True

    def set_service_state(self, service, state):
        state_command = {
            "started": "start",
            "stopped": "stop",
            "restarted": "restart",
            "reloaded": "reload"
        }[state]
        rc, out, err = self.module.run_command(
            f"{self.dinitctl} {state_command} {service}",
            check_rc = True
        )

        changed = True
        if state in ("started", "stopped") and "already" in out:
            changed = False
        if changed:
            self.result["changed"] = True


def main():
    DinitModule().run()


if __name__ == "__main__":
    main()
