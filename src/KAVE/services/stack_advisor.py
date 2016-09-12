#!/usr/bin/env ambari-python-wrap
##############################################################################
#
# Copyright 2016 KPMG Advisory N.V. (unless otherwise stated)
#
# Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
##############################################################################


class HDP24KAVE22StackAdvisor(HDP24StackAdvisor):

    # List of validators which should also be evaluated if there is not recommended default present.
    validateWithoutRecommendedDefault = ['freeipa']

    def validatorPasswordStrength(self, properties, propertyName, minLength=8):
        if propertyName not in properties:
            return self.getErrorItem("Value should be set")
        if len(properties[propertyName]) < minLength:
            return self.getErrorItem("Password should be at least %s chars long" % minLength)
        return None

    def getServiceConfigurationValidators(self):
        parentValidators = super(HDP24KAVE22StackAdvisor, self).getServiceConfigurationValidators()
        childValidators = {
            "FREEIPA": {"freeipa": self.validateFreeIPAConfigurations}
        }
        parentValidators.update(childValidators)
        return parentValidators

    def validateFreeIPAConfigurations(self, properties, recommendedDefaults, configurations):
        validationItems = [{"config-name": 'directory_password',
                            "item": self.validatorPasswordStrength(properties, 'directory_password')},
                           {"config-name": 'ldap_bind_password',
                            "item": self.validatorPasswordStrength(properties, 'ldap_bind_password')}
                           ]
        return self.toConfigurationValidationProblems(validationItems, "freeipa")
