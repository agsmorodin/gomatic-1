from xml.etree import ElementTree as ET
from gomatic.mixins import CommonEqualityMixin
from gomatic.xml_operations import PossiblyMissingElement, Ensurance

import uuid
import urllib
from collections import OrderedDict


class GenericArtifactoryRepositoryPackage(CommonEqualityMixin):
    def __init__(self, element):
        self.element = element

        if not self._id:
            self._id = uuid.uuid1()
        self._repository_name = None

    def __repr__(self):
        return 'GenericArtifactoryRepositoryPackage("%s")' % self.name

    @property
    def name(self):
        return self.element.attrib['name']

    @property
    def _id(self):
        return self.element.attrib.get('id')

    @_id.setter
    def _id(self, value):
        Ensurance(self.element).set('id', value)

    @property
    def repository_name(self):
        return self._repository_name

    @repository_name.setter
    def repository_name(self, value):
        self._repository_name = value

    def to_dict(self, ordered=False):
        if ordered:
            result = OrderedDict()
        else:
            result = {}
        result['type'] = 'artifactory'
        result['repository_name'] = self.repository_name
        result['name'] = self.name
        result['id'] = self._id
        result['configuration'] = {
            'repository_id': self.repository_id,
            'package_path': self.package_path,
            'package_id': self.package_id,
	    'poll_version_from': self.poll_version_from,
            'poll_version_to': self.poll_version_to
        }
        return result

    def make_empty(self):
        PossiblyMissingElement(self.element).remove_all_children()

    def set_configuration_property(self, name, value):
        config = Ensurance(self.element).ensure_child('configuration')
        new_element = ET.fromstring('<property><key>%s</key><value>%s</value></property>' % (name, value))
        config.append(new_element)

    def remove_configuration_property(self, name):
        config = Ensurance(self.element).ensure_child('configuration')
        matching = [p for p in config.element.findall('property') if p.find('key').text == name]
        if matching:
            [config.element.remove(p) for p in matching]
        return self

    def get_configuration_property(self, name):
        config = Ensurance(self.element).ensure_child('configuration')
        matching = [
            p for p in config.element.findall('property')
            if p.find('key').text == name
        ]
        if matching:
            return matching[0].find('value').text

    @property
    def repository_id(self):
        return self.get_configuration_property('REPO_ID')

    @repository_id.setter
    def repository_id(self, value):
        self.remove_configuration_property('REPO_ID')
        self.set_configuration_property('REPO_ID', value)

    @property
    def package_path(self):
        return self.get_configuration_property('PACKAGE_PATH')

    @package_path.setter
    def package_path(self, value):
        self.remove_configuration_property('PACKAGE_PATH')
        self.set_configuration_property('PACKAGE_PATH', value)

    @property
    def poll_version_from(self):
	return self.get_configuration_property('POLL_VERSION_FROM')
	
    @poll_version_from.setter
    def poll_version_from(self, value):
        self.remove_configuration_property('POLL_VERSION_FROM')
        self.set_configuration_property('POLL_VERSION_FROM', value)

    @property
    def poll_version_to(self):
        return self.get_configuration_property('POLL_VERSION_TO')

    @poll_version_to.setter
    def poll_version_from(self, value):
        self.remove_configuration_property('POLL_VERSION_TO')
        self.set_configuration_property('POLL_VERSION_TO', value)

    @property
    def package_id(self):
        return self.get_configuration_property('PACKAGE_ID')

    @package_id.setter
    def package_id(self, value):
        self.remove_configuration_property('PACKAGE_ID')
        self.set_configuration_property('PACKAGE_ID', value)


class GenericArtifactoryRepository(CommonEqualityMixin):
    def __init__(self, element):
        self.element = element

        if not self.has_id:
            self.__set_id()
        Ensurance(self.element).ensure_child_with_attribute('pluginConfiguration', 'id', 'generic-artifactory').set('version', '1')

    def __repr__(self):
        return 'GenericArtifactoryRepository("%s")' % self.name

    @property
    def name(self):
        return self.element.attrib['name']

    def make_empty(self):
        PossiblyMissingElement(self.element).remove_all_children()

    @property
    def has_id(self):
        return 'id' in self.element.attrib

    def __set_id(self):
        Ensurance(self.element).set('id', str(uuid.uuid1()))

    def set_configuration_property(self, name, value, encrypted=False):

        config = Ensurance(self.element).ensure_child('configuration')
        if encrypted:
            new_element = ET.fromstring('<property><key>%s</key><encryptedValue>%s</encryptedValue></property>' % (name, value))
        else:
            new_element = ET.fromstring('<property><key>%s</key><value>%s</value></property>' % (name, value))
        config.append(new_element)

    def set_encrypted_configuration_property(self, name, encrypted_value):
        self.set_configuration_property(name, encrypted_value, encrypted=True)

    def remove_configuration_proporty(self, name):
        config = Ensurance(self.element).ensure_child('configuration')
        matching = [p for p in config.element.findall('property') if p.find('key').text == name]
        if matching:
            [config.element.remove(p) for p in matching]
        return self

    def set_repository_url(self, repository_url):
        self.remove_configuration_proporty('REPO_URL')
        self.set_configuration_property('REPO_URL', repository_url)
        return self

    def set_credentials(self, username, password):
        self.remove_configuration_proporty('USERNAME')
        self.remove_configuration_proporty('PASSWORD')
        self.set_configuration_property('USERNAME', urllib.quote(username, safe=''))
        self.set_encrypted_configuration_property('PASSWORD', password)
        return self

    @property
    def generic_artifactory_repository_packages(self):
        return [GenericArtifactoryRepositoryPackage(e) for e in self.element.findall('packages')[0].findall('package')]

    def ensure_generic_artifactory_repository_package(self, package_name):
        package_element = Ensurance(self.element).ensure_child('packages').ensure_child_with_attribute("package", "name", package_name)
        package = GenericArtifactoryRepositoryPackage(package_element.element)
        # package.make_configuration_empty()
        return package

    def ensure_removal_generic_artifactory_repository_package(self, package_name):
        matching = [p for p in self.generic_artifactory_repository_packages if p.name == package_name]
        for package in matching:
            self.element.findall('packages')[0].remove(package.element)
        return self

    def ensure_replacement_generic_artifactory_repository_package(self, package_name):
        package = self.ensure_generic_artifactory_repository_package(package_name)
        package.make_empty()
        return package
