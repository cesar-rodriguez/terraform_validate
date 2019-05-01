import hcl
import os
import codecs
import re
import traceback
import json
import logging


class TerraformPropertyList:

    def __init__(self, validator):
        self.properties = []
        self.validator = validator

    def tfproperties(self):
        return self.properties

    def property(self, property_name):
        propList = TerraformPropertyList(self.validator)
        for property in self.properties:
            pvList = []
            if type(property.property_value) is list:
                pvList = property.property_value
            else:
                pvList.append(property.property_value)

            for pv in pvList:
                if property_name in pv.keys():
                    propList.properties.append(TerraformProperty(property.resource_type,
                                               "{0}.{1}".format(property.resource_name, property.property_name),
                                               property_name,
                                               pv[property_name],
                                               property.moduleName,
                                               property.fileName))
                elif self.validator.raise_error_if_property_missing:
                    self.validator.preprocessor.add_failure(
                        "[{0}.{1}] should have property: '{2}'".format(property.resource_type, "{0}.{1}".format(property.resource_name, property.property_name), property_name),
                        property.moduleName,
                        property.fileName,
                        self.validator.severity)

        return propList

    def should_equal_case_insensitive(self, expected_value):
        self.should_equal(expected_value, True)

    def should_equal(self, expected_value, caseInsensitive=False):
        for property in self.properties:

            expected_value = self.int2str(expected_value)
            property.property_value = self.int2str(property.property_value)
            expected_value = self.bool2str(expected_value)
            property.property_value = self.bool2str(property.property_value)

            if caseInsensitive:
                # make both actual and expected lower case so case won't matter
                pv = property.property_value.lower()
                ev = expected_value.lower()
            else:
                pv = property.property_value
                ev = expected_value

            if pv != ev:
                self.validator.preprocessor.add_failure("[{0}.{1}.{2}] should be '{3}'. Is: '{4}'".format(property.resource_type,
                                                                                                          property.resource_name,
                                                                                                          property.property_name,
                                                                                                          expected_value,
                                                                                                          property.property_value),
                                                        property.moduleName,
                                                        property.fileName,
                                                        self.validator.severity)

    def should_not_equal_case_insensitive(self, expected_value):
        self.should_not_equal(expected_value, True)

    def should_not_equal(self, expected_value, caseInsensitive=False):
        for property in self.properties:

            property.property_value = self.int2str(property.property_value)
            expected_value = self.int2str(expected_value)
            expected_value = self.bool2str(expected_value)
            property.property_value = self.bool2str(property.property_value)

            if caseInsensitive:
                # make both actual and expected lower case so case won't matter
                pv = property.property_value.lower()
                ev = expected_value.lower()
            else:
                pv = property.property_value
                ev = expected_value

            if pv == ev:
                self.validator.preprocessor.add_failure("[{0}.{1}.{2}] should not be '{3}'. Is: '{4}'".format(property.resource_type,
                                                                                                              property.resource_name,
                                                                                                              property.property_name,
                                                                                                              expected_value,
                                                                                                              property.property_value),
                                                        property.moduleName,
                                                        property.fileName,
                                                        self.validator.severity)

    def list_should_contain(self, values_list):
        if type(values_list) is not list:
            values_list = [values_list]

        for property in self.properties:

            values_missing = []
            for value in values_list:
                if value not in property.property_value:
                    values_missing.append(value)

            if len(values_missing) != 0:
                if type(property.property_value) is list:
                    property.property_value = [str(x) for x in property.property_value]  # fix 2.6/7
                self.validator.preprocessor.add_failure("[{0}.{1}.{2}] '{3}' should contain '{4}'.".format(property.resource_type,
                                                                                                           property.resource_name,
                                                                                                           property.property_name,
                                                                                                           property.property_value,
                                                                                                           values_missing),
                                                        property.moduleName,
                                                        property.fileName,
                                                        self.validator.severity)

    def list_should_not_contain(self, values_list):
        if type(values_list) is not list:
            values_list = [values_list]

        for property in self.properties:

            values_missing = []
            for value in values_list:
                if value in property.property_value:
                    values_missing.append(value)

            if len(values_missing) != 0:
                if type(property.property_value) is list:
                    property.property_value = [str(x) for x in property.property_value]  # fix 2.6/7
                self.validator.preprocessor.add_failure("[{0}.{1}.{2}] '{3}' should not contain '{4}'.".format(property.resource_type,
                                                                                                               property.resource_name,
                                                                                                               property.property_name,
                                                                                                               property.property_value,
                                                                                                               values_missing),
                                                        property.moduleName,
                                                        property.fileName,
                                                        self.validator.severity)

    def should_have_properties(self, properties_list):
        if type(properties_list) is not list:
            properties_list = [properties_list]

        for property in self.properties:
            property_names = property.property_value.keys()
            for required_property_name in properties_list:
                if required_property_name not in property_names:
                    self.validator.preprocessor.add_failure("[{0}.{1}.{2}] should have property: '{3}'".format(property.resource_type,
                                                                                                               property.resource_name,
                                                                                                               property.property_name,
                                                                                                               required_property_name),
                                                            property.moduleName,
                                                            property.fileName,
                                                            self.validator.severity)

    def should_not_have_properties(self, properties_list):
        if type(properties_list) is not list:
            properties_list = [properties_list]

        for property in self.properties:
            property_names = property.property_value.keys()
            for excluded_property_name in properties_list:
                if excluded_property_name in property_names:
                    self.validator.preprocessor.add_failure("[{0}.{1}.{2}] should not have property: '{3}'".format(property.resource_type,
                                                                                                                   property.resource_name,
                                                                                                                   property.property_name,
                                                                                                                   excluded_property_name),
                                                            property.moduleName,
                                                            property.fileName,
                                                            self.validator.severity)

    def find_property(self, regex):
        list = TerraformPropertyList(self.validator)
        for property in self.properties:
            for nested_property in property.property_value:
                if self.validator.matches_regex_pattern(nested_property, regex):
                    list.properties.append(TerraformProperty(property.resource_type,
                                           "{0}.{1}".format(property.resource_name, property.property_name),
                                           nested_property,
                                           property.property_value[nested_property],
                                           property.moduleName,
                                           property.fileName))
        return list

    def should_match_regex(self, regex):
        for property in self.properties:
            if not self.validator.matches_regex_pattern(property.property_value, regex):
                self.validator.preprocessor.add_failure("[{0}.{1}] should match regex '{2}'".format(property.resource_type, "{0}.{1}".format(property.resource_name, property.property_name), regex),
                                                        property.moduleName,
                                                        property.fileName,
                                                        self.validator.severity)

    def should_contain_valid_json(self):
        for property in self.properties:
            try:
                json.loads(property.property_value)
            except:
                self.validator.preprocessor.add_failure("[{0}.{1}.{2}] is not valid json".format(property.resource_type, property.resource_name, property.property_name),
                                                        property.moduleName,
                                                        property.fileName,
                                                        self.validator.severity)

    def bool2str(self, bool):
        if str(bool).lower() in ["true"]:
            return "True"
        if str(bool).lower() in ["false"]:
            return "False"
        return bool

    def int2str(self, property_value):
        if type(property_value) is int:
            property_value = str(property_value)
        return property_value


class TerraformProperty:

    def __init__(self, resource_type, resource_name, property_name, property_value, moduleName, fileName):
        self.resource_type = resource_type
        self.resource_name = resource_name
        self.property_name = property_name
        self.property_value = property_value
        self.moduleName = moduleName
        self.fileName = fileName


class TerraformResource:

    def __init__(self, type, name, config, fileName, moduleName):
        self.type = type
        self.name = name
        self.config = config
        self.fileName = fileName
        self.moduleName = moduleName


class TerraformResourceList:

    def __init__(self, validator, requestedResourceType, resourceTypes, resources):
        self.validator = validator
        self.resource_list = []
        self.requestedResourceType = requestedResourceType

        resourcesByType = {}
        for resourceName in resources:
            resource = resources[resourceName]
            resourceType = resource.type
            resourcesByType[resourceType] = resourcesByType.get(resourceType, {})
            resourcesByType[resourceType][resourceName] = resource.config

        if type(requestedResourceType) is str:
            resourceTypes = []
            for resourceType in resourcesByType:
                if validator.matches_regex_pattern(resourceType, requestedResourceType):
                    resourceTypes.append(resourceType)
        elif requestedResourceType is not None:
            resourceTypes = requestedResourceType

        for resourceType in resourceTypes:
            if resourceType in resourcesByType.keys():
                for resourceName in resourcesByType[resourceType]:
                    self.resource_list.append(
                        TerraformResource(resourceType, resourceName, resourcesByType[resourceType][resourceName], resources[resourceName].fileName, resources[resourceName].moduleName))

        self.resource_types = resourceTypes

    def property(self, property_name):
        list = TerraformPropertyList(self.validator)
        if len(self.resource_list) > 0:
            for resource in self.resource_list:
                if property_name in resource.config.keys():
                    list.properties.append(TerraformProperty(resource.type, resource.name, property_name, resource.config[property_name], resource.moduleName, resource.fileName))
                elif self.validator.raise_error_if_property_missing:
                    self.validator.preprocessor.add_failure("[{0}.{1}] should have property: '{2}'".format(resource.type, resource.name, property_name),
                                                            resource.moduleName, resource.fileName, self.validator.severity)

        return list

    def find_property(self, regex):
        list = TerraformPropertyList(self.validator)
        if len(self.resource_list) > 0:
            for resource in self.resource_list:
                for property in resource.config:
                    if self.validator.matches_regex_pattern(property, regex):
                        list.properties.append(TerraformProperty(resource.type,
                                                                 resource.name,
                                                                 property,
                                                                 resource.config[property],
                                                                 resource.moduleName,
                                                                 resource.fileName))
        return list

    def with_property(self, property_name, regex):
        list = TerraformResourceList(self.validator, None, self.resource_types, {})

        if len(self.resource_list) > 0:
            for resource in self.resource_list:
                for property in resource.config:
                    if property == property_name:
                        tf_property = TerraformProperty(resource.type, resource.name, property_name, resource.config[property_name], resource.moduleName, resource.fileName)
                        if self.validator.matches_regex_pattern(tf_property.property_value, regex):
                            list.resource_list.append(resource)

        return list

    def should_not_exist(self):
        for terraformResource in self.resource_list:
            if terraformResource.type == self.requestedResourceType:
                self.validator.preprocessor.add_failure("[{0}] should not exist. Found in resource named {1}".format(self.requestedResourceType, terraformResource.name),
                                                        terraformResource.moduleName, terraformResource.fileName, self.validator.severity)

    def should_have_properties(self, properties_list):
        if type(properties_list) is not list:
            properties_list = [properties_list]

        if len(self.resource_list) > 0:
            for resource in self.resource_list:
                property_names = resource.config.keys()
                for required_property_name in properties_list:
                    if required_property_name not in property_names:
                        self.validator.preprocessor.add_failure("[{0}.{1}] should have property: '{2}'".format(
                            resource.type, resource.name, required_property_name),
                            resource.moduleName, resource.fileName, self.validator.severity)

    def should_not_have_properties(self, properties_list):
        if type(properties_list) is not list:
            properties_list = [properties_list]

        if len(self.resource_list) > 0:
            for resource in self.resource_list:
                property_names = resource.config.keys()
                for excluded_property_name in properties_list:
                    if excluded_property_name in property_names:
                        self.validator.preprocessor.add_failure("[{0}.{1}] should not have property: '{2}'".format(resource.type, resource.name, excluded_property_name),
                                                                resource.moduleName, resource.fileName, self.validator.severity)

    def name_should_match_regex(self, regex):
        for resource in self.resource_list:
            if not self.validator.matches_regex_pattern(resource.name, regex):
                self.validator.preprocessor.add_failure("[{0}.{1}] name should match regex: '{2}'".format(resource.type, resource.name, regex),
                                                        resource.moduleName, resource.fileName, self.validator.severity)


class Validator:

    # default severity is high
    severity = "high"
    preprocessor = None

    def __init__(self):
        self.raise_error_if_property_missing = False

    def resources(self, type):
        resources = self.terraform.get('resource', {})

        return TerraformResourceList(self, type, None, resources)

    def error_if_property_missing(self):
        self.raise_error_if_property_missing = True

    # generator that loops through all files to be scanned (stored internally in fileName; returns self (Validator) but sets self.fileName and self.terraform
    def get_terraform_files(self):
        for self.fileName, self.terraform in self.preprocessor.modulesDict.items():
            yield self

    def matches_regex_pattern(self, variable, regex):
        return not (self.get_regex_matches(regex, variable) is None)

    def get_regex_matches(self, regex, variable):
        if regex[-1:] != "$":
            regex = regex + "$"

        if regex[0] != "^":
            regex = "^" + regex

        variable = str(variable)
        if '\n' in variable:
            return re.match(regex, variable, re.DOTALL)
        return re.match(regex, variable)

    # this is only used by unit_test.py
    def setTerraform(self, terraform):
        self.terraform = terraform
        self.fileName = "none.tf"


class PreProcessor:

    TF = ".tf"
    UTF8 = "utf8"
    IS_MODULE = "__isModule__"
    PARENT = "__parent__"
    MODULE_NAME = "__ModuleName__"
    FILE_NAME = "__fileName__"
    LOCALS = "locals"
    VARIABLE = "variable"
    OUTPUT = "output"
    RESOURCE = "resource"
    VALUE = "value"
    MODULE = "module"
    SOURCE = "source"
    DEFAULT = "default"
    REGEX_HEREDOC_PATTERN = re.compile('<<\S+\r?\n')

    def __init__(self, jsonOutput):
        self.jsonOutput = jsonOutput
        self.variablesFromCommandLine = {}
        self.hclDict = {}
        self.modulesDict = {}
        self.fileNames = {}
        self.passNumber = 1
        self.dummyIndex = 0
        # on 1st pass replace ${ with @{
        # on 2nd pass replace ${ and @{ with !(
        self.variableFind = "${"
        self.variableErrorReplacement = "@{"

    def process(self, path, variablesJsonFilename=None):
        if variablesJsonFilename is not None:
            with open(variablesJsonFilename) as variablesJsonFile:
                self.variablesFromCommandLine = json.load(variablesJsonFile)

        self.root = None
        self.readDir(path, self.hclDict)

        # all terraform files are now loaded into hclDict (indexed by subdirectory/fileName/terraform structure)
        # process hclDict and load every module into modulesDict
        self.getAllModules(self.hclDict, False)
        # make second pass so variables depending on a previous definition should now be defined
        logging.warning("------------------>>>starting pass 2...")
        self.passNumber = 2
        self.variableFind = self.variableErrorReplacement
        self.variableErrorReplacement = "!{"
        self.getAllModules(self.hclDict, False)

    def readDir(self, path, d):
        for directory, subdirectories, files in os.walk(path):
            if self.root is None:
                self.root = directory
                i = self.root.rfind(os.path.sep)
                if i != -1:
                    self.root = self.root[i+1:]
                # define root and mark this dictionary as a module since all directories in terraform are modules by default
                self.hclDict[self.root] = {}
                self.hclDict[self.root][self.IS_MODULE] = True
                self.hclDict[self.root][self.PARENT] = None
                self.hclDict[self.root][self.MODULE_NAME] = self.root
                d = self.hclDict[self.root]

            for file in files:
                if file[-3:].lower() == self.TF:
                    # terraform file (ends with .tf)
                    fileName = os.path.join(directory, file)
                    relativeFileName = fileName[len(path):]
                    if os.path.getsize(fileName) != 0:
                        with codecs.open(fileName, 'r', encoding='utf8') as fp:
                            try:
                                terraform_string = fp.read()
                                self.loadFileByDir(fileName, relativeFileName, d, d, terraform_string)
                                self.fileNames[fileName] = fileName
                            except:
                                self.add_error(traceback.format_exc(), "---", fileName, "high")

    # load file by directory, marking each directory as a module and setting parent directories
    def loadFileByDir(self, fileName, path, hclSubDirDict, parentDir, terraform_string):
        i = path.find("\\")
        if i == -1:
            # \ not found, try /
            i = path.find("/")
            if i == -1:
                # end of subdirectories; path is a terraform filename; load terraform file into dictionary
                hclSubDirDict[path] = hcl.loads(terraform_string)
                hclSubDirDict[path][self.FILE_NAME] = fileName
                # remove file name from end of path
                t = self.getPreviousLevel(fileName, os.path.sep)
                self.findModuleSources(hclSubDirDict[path], parentDir, t[0])
                return
        if i == 0:
            # found in first character, recursively try again skipping first character
            self.loadFileByDir(fileName, path[1:], hclSubDirDict, parentDir, terraform_string)
        else:
            # get subdirectory
            subdir = path[:i]
            if hclSubDirDict.get(subdir) is None:
                # subdirectory not defined in our dictionary yet so define it
                hclSubDirDict[subdir] = {}
                hclSubDir = hclSubDirDict[subdir]
                # mark this dictionary as a module since all directories in terraform are modules by default
                hclSubDir[self.IS_MODULE] = True
                hclSubDir[self.PARENT] = parentDir
                hclSubDir[self.MODULE_NAME] = subdir
            else:
                hclSubDir = hclSubDirDict[subdir]
            # recursively process next subdirectory
            i += 1
            self.loadFileByDir(fileName, path[i:], hclSubDirDict[subdir], hclSubDir, terraform_string)

    def findModuleSources(self, d, parentDir, currentFileName):
        for key in d:
            # only process module key
            if key == self.MODULE:
                modules = d[key]
                # process all modules
                for moduleName in modules:
                    module = modules[moduleName]
                    # find source parameter
                    for parameter in module:
                        if parameter == self.SOURCE:
                            sourcePath = module[parameter]
                            self.createMissingFromSourcePath(sourcePath, parentDir, currentFileName)

    def createMissingFromSourcePath(self, sourcePath, d, currentFileName):
        # source is local
        while sourcePath != "":
            t = self.getNextLevel(sourcePath, "/")
            currentModule = t[0]
            sourcePath = t[1]
            if currentModule == "..":
                # move up a level
                t = self.getPreviousLevel(currentFileName, os.path.sep)
                currentFileName = t[0]
                if d.get(self.PARENT) is None:
                    # add parent
                    self.dummyIndex += 1
                    parent = {}
                    parent[self.PARENT] = None
                    parent[self.IS_MODULE] = True
                    parent[self.MODULE_NAME] = "dummy" + str(self.dummyIndex)
                    parent[d[self.MODULE_NAME]] = d
                    d[self.PARENT] = parent
                    self.hclDict = parent
                d = d[self.PARENT]
            elif currentModule == ".":
                # current directory; do nothing
                pass
            else:
                # move down to currentModule level
                currentFileName += os.path.sep + currentModule
                md = d.get(currentModule, False)
                if md is False:
                    # create new level
                    d[currentModule] = {}
                    md = d[currentModule]
                    md[self.PARENT] = d
                    md[self.MODULE_NAME] = currentModule
                    md[self.IS_MODULE] = True

                d = md
        # read directory
        self.readDir(currentFileName, d)
        return d

    # get all modules for given dictionary d; pass isModule as True if in a module block
    def getAllModules(self, d, isModule):
        for key in d:
            # ignore parent key
            if key != self.PARENT:
                value = d[key]
                if type(value) is dict:
                    if isModule or self.isModule(value):
                        moduleName = key
                        # load module, resolve variables in it and add it to modules dictionary
                        moduleDict = self.getModule(moduleName)
                        if self.isModule(value):
                            moduleDict[self.PARENT] = d[moduleName][self.PARENT]
                    # recursively get all modules in the nested dictionary in value
                    self.getAllModules(value, key == "module")

    # get given moduleName from modulesDict; find & load it if not there yet
    def getModule(self, moduleName, errorIfNotFound=True, dictToCopyFrom=None, tfDict=None):
        moduleDict = self.modulesDict.get(moduleName)
        if moduleDict is None or (moduleDict[self.VARIABLE] == {} and moduleDict[self.LOCALS] == {} and moduleDict[self.OUTPUT] == {}):
            # not there yet, find it and load it
            moduleDict = self.findModule(moduleName, self.hclDict, dictToCopyFrom, tfDict)
            if moduleDict is None:
                # couldn't find it, log it and create a dummy entry
                if errorIfNotFound:
                    self.logMsg("error", "Couldn't find module " + moduleName)
                moduleDict = self.createModuleEntry(moduleName)
        elif self.passNumber > 1:
            # module found on second pass, re-resolve variables
            self.findModule(moduleName, self.hclDict, dictToCopyFrom, tfDict)

        return moduleDict

    # find given moduleName in given dictionary d; load module attributes and resolve variables in module; last two parameters are all or nothing
    def findModule(self, moduleName, d, dictToCopyFrom=None, tfDict=None):
        # use dictToCopyFrom if provided
        if dictToCopyFrom is not None:
            sourcePath = self.getSourcePath(dictToCopyFrom)
            if sourcePath is not None and not sourcePath.startswith("git::"):
                dd = self.getModuleDictFromSourcePath(sourcePath, tfDict)
                if dd:
                    moduleDict = self.modulesDict.get(dd[self.MODULE_NAME])
                    if moduleDict is None:
                        moduleDict = self.createModuleEntry(dd[self.MODULE_NAME])
                        moduleDict[self.IS_MODULE] = True
                    self.loadModule(moduleName, dd, dictToCopyFrom)
                    self.loadModule(dd[self.MODULE_NAME], dd, dictToCopyFrom)
                    # source module found, replace variables and return it
                    m = self.loadModule(dd[self.MODULE_NAME], dd, dictToCopyFrom)
                    return m
            return self.loadModule(moduleName, {}, dictToCopyFrom)

        for key in d:
            # ignore parent key
            if key != self.PARENT:
                value = d[key]
                if key == moduleName:
                    # module found, replace variables and return it
                    return self.loadModule(moduleName, value, dictToCopyFrom)
                else:
                    if type(value) is dict:
                        if self.isModule(value):
                            # recursively find the module
                            m = self.findModule(moduleName, value)
                            if m is not None:
                                return m
        # not found
        return None

    def loadModule(self, moduleName, d, dictToCopyFrom):
        self.logMsg("warning", ">>>loading module " + moduleName)

        moduleDict = self.modulesDict.get(moduleName)
        if moduleDict is None:
            # create empty module entry
            moduleDict = self.createModuleEntry(moduleName)
            moduleDict[self.IS_MODULE] = self.hasTerraform(d)

        if dictToCopyFrom is not None:
            mdv = moduleDict[self.VARIABLE]
            # add/replace the passed in variables to the module's variables
            for attr in dictToCopyFrom:
                if attr != self.SOURCE:
                    mdv[attr] = dictToCopyFrom[attr]

        # load all attributes for this module
        self.loadModuleAttributes(moduleName, d, moduleDict, None)
        # resolve variables for this module
        self.resolveVariablesInModule(moduleName, moduleDict)
        return moduleDict

    def createModuleEntry(self, moduleName):
        self.modulesDict[moduleName] = {}
        moduleDict = self.modulesDict[moduleName]
        moduleDict[self.VARIABLE] = {}
        moduleDict[self.LOCALS] = {}
        moduleDict[self.OUTPUT] = {}
        moduleDict[self.RESOURCE] = {}
        moduleDict[self.IS_MODULE] = False
        return moduleDict

    def loadModuleAttributes(self, moduleName, d, moduleDict, tfDict):
        if self.isModule(d):
            if tfDict is None:
                tfDict = d
            else:
                # skip nested modules
                return

        for key in sorted(d):
            # ignore parent key
            if key != self.PARENT:
                value = d[key]
                if key == self.LOCALS:
                    # get values for all local variables
                    for local in value:
                        moduleDict[self.LOCALS][local] = value[local]
                elif key == self.OUTPUT:
                    for output in value:
                        moduleDict[self.OUTPUT][output] = value[output][self.VALUE]
                elif key == self.RESOURCE:
                    if self.passNumber == 1:
                        for resourceType in value:
                            resourceNames = value[resourceType]
                            for resourceName in resourceNames:
                                config = resourceNames[resourceName]
                                moduleDict[self.RESOURCE][resourceName] = TerraformResource(resourceType, resourceName, config, d[self.FILE_NAME], moduleName)
                elif key == self.VARIABLE:
                    # initialize any default values for variables
                    for variable in value:
                        if value[variable].get(self.DEFAULT) is not None:
                            moduleDict[self.VARIABLE][variable] = value[variable][self.DEFAULT]
                elif key == self.MODULE:
                    # loop through all modules
                    for mn in value:
                        # resolve parameter variables first
                        for parameter in value[mn]:
                            if parameter != self.SOURCE:
                                replacementValue = self.resolveVariableByType(value[mn][parameter], moduleName)
                                if replacementValue != value[mn][parameter]:
                                    self.logMsg("warning", "replaced module " + mn + " parameter " + parameter + " value " + str(value[mn][parameter]) + " with " + str(replacementValue))
                                    value[mn][parameter] = replacementValue
                        # get defined module; load it if not already there
                        md = self.getModule(mn, False, value[mn], tfDict)
                        # copy all outputs from source module (md) to containing module variable
                        for output in md[self.OUTPUT]:
                            # only copy if not already there
                            if moduleDict[self.VARIABLE].get(output) is None:
                                moduleDict[self.VARIABLE][output] = md[self.OUTPUT][output]
                else:
                    if type(value) is dict:
                        # don't load any other nested modules
                        if not self.isModule(value):
                            self.loadModuleAttributes(moduleName, value, moduleDict, tfDict)

    def getSourcePath(self, parameterDict):
        for parameter in parameterDict:
            if parameter == self.SOURCE:
                return parameterDict[parameter]
        return None

    def getModuleDictFromSourcePath(self, sourcePath, d):
        # source is local
        while sourcePath != "":
            t = self.getNextLevel(sourcePath, "/")
            currentModule = t[0]
            sourcePath = t[1]
            if currentModule == "..":
                # move up a level
                d = d[self.PARENT]
            elif currentModule == ".":
                # current directory; do nothing
                pass
            else:
                # move down to currentModule level
                d = d.get(currentModule, False)
                if d is False:
                    return False
        return d

    # resolve variables (anything surrounded by ${}) in given moduleDict
    def resolveVariablesInModule(self, moduleName, moduleDict):
        self.shouldLogErrors = False
        # resolve variables
        for key in moduleDict[self.VARIABLE]:
            value = moduleDict[self.VARIABLE][key]
            replacementValue = self.resolveVariableByType(value, moduleName)
            moduleDict[self.VARIABLE][key] = replacementValue
            if replacementValue != value:
                self.logMsg("warning", "replaced variable " + key + " value " + str(value) + " with " + str(replacementValue))
        # resolve locals
        for key in moduleDict[self.LOCALS]:
            value = moduleDict[self.LOCALS][key]
            replacementValue = self.resolveVariableByType(value, moduleName)
            moduleDict[self.LOCALS][key] = replacementValue
            if replacementValue != value:
                self.logMsg("warning", "replaced local variable " + key + " value " + str(value) + " with " + str(replacementValue))
        # resolve outputs
        for key in moduleDict[self.OUTPUT]:
            value = moduleDict[self.OUTPUT][key]
            replacementValue = self.resolveVariableByType(value, moduleName)
            moduleDict[self.OUTPUT][key] = replacementValue
            if replacementValue != value:
                self.logMsg("warning", "replaced output variable " + key + " value " + str(value) + " with " + str(replacementValue))
        # resolve resources
        self.shouldLogErrors = True
        for key in moduleDict[self.RESOURCE]:
            value = moduleDict[self.RESOURCE][key].config
            replacementValue = self.resolveVariableByType(value, moduleName)
            moduleDict[self.RESOURCE][key].config = replacementValue
            if replacementValue != value:
                self.logMsg("warning", "replaced resource variable " + key + " value " + str(value) + " with " + str(replacementValue))

    def resolveVariableByType(self, value, moduleName):
        if type(value) is str:
            return self.resolveVariableLine(value, moduleName, True)
        elif type(value) is dict:
            return self.resolveDictVariable(value, moduleName)
        elif type(value) is list:
            return self.resolveListVariable(value, moduleName)
        else:
            return value

    def resolveDictVariable(self, value, moduleName):
        returnValue = {}
        for key in value:
            returnValue[key] = self.resolveVariableByType(value[key], moduleName)
        return returnValue

    def resolveListVariable(self, value, moduleName):
        index = 0
        for v in value:
            value[index] = self.resolveVariableByType(v, moduleName)
            index += 1
        return value

    # returns True if given dictionary d contains a key of __isModule__
    def isModule(self, d):
        for key in d:
            if key == self.IS_MODULE:
                return d[key]
        return False

    # returns True if given dictionary d contains at least one terraform file
    def hasTerraform(self, d):
        for key in d:
            if key.lower().endswith(self.TF):
                return True
        return False

    # resolve entire variable
    def resolveVariableLine(self, value, moduleName, findShouldRecurse, dictToCopyFrom=None, tfDict=None):
        # find variable (not in brackets)
        t = self.findVariable(value, False, False, None)
        if t is None:
            return value
        # a variable needs to be replaced
        var = t[0]
        b = t[1]
        e = t[2]
        rv = self.resolveVariable(var, moduleName, findShouldRecurse, dictToCopyFrom, tfDict)
        if b == 0 and e == len(value):
            # full replacement; don't merge since a string may not have been returned
            newValue = rv[0]
        else:
            newValue = value[:b] + str(rv[0]) + value[e:]
        findShouldRecurse = rv[1]

        # recursively resolve the variables since there may be more than one variable in this variable
        return self.resolveVariableLine(newValue, moduleName, findShouldRecurse)

    # resolve innermost variable
    def resolveVariable(self, value, moduleName, findShouldRecurse, dictToCopyFrom=None, tfDict=None):
        # find variable (possibly in brackets)
        t = self.findVariable(value, findShouldRecurse, False, None)
        v = t[0]
        b = t[1]
        e = t[2]
        isDollarBrace = v.startswith(self.variableFind)
        if isDollarBrace:
            # inside ${}
            var = v[2:len(v)-1]
        else:
            # inside []
            var = v[1:len(v)-1]
        # update moduleName in case we switch modules and need to recurse more
        replacementValue, moduleName, isHandledType = self.getReplacementValue(var, moduleName, dictToCopyFrom, tfDict)
        if replacementValue == var:
            # couldn't find a replacement; change to our notation to mark it
            if isDollarBrace:
                if isHandledType:
                    self.logMsg("error", "Couldn't find a replacement for: " + var + " in " + moduleName)
                else:
                    self.logMsg("debug", "Couldn't find a replacement for: " + var + " in " + moduleName)
                replacementValue = value[:b] + self.variableErrorReplacement + var + value[e-1:]
            else:
                # ignore if inside brackets
                replacementValue = value[:b+1] + var + value[e-1:]
            return (replacementValue, isDollarBrace)

        if type(replacementValue) is str:
            if isDollarBrace:
                if v == replacementValue:
                    # this prevents a loop
                    replacementValue = replacementValue.replace(self.variableFind, self.variableErrorReplacement, 1)
                    self.logMsg("debug", "Couldn't find a replacement for: " + var + " (would have looped) in " + moduleName)
                else:
                    self.logMsg("info", "  replacing ${" + var + "} with " + replacementValue)
                    # resolve the variable again since the replacement may also contain variables
                    return (self.resolveVariableLine(replacementValue, moduleName, findShouldRecurse), isDollarBrace)
            else:
                self.logMsg("info", "  replacing [" + var + "] with " + replacementValue)
                b += 1
                e -= 1
                # resolve the variable again since the replacement may also contain variables
                return (value[:b] + self.resolveVariableLine(replacementValue, moduleName, findShouldRecurse) + value[e:], isDollarBrace)
        elif type(replacementValue) is dict:
            bb = var.find("[")
            if bb == -1:
                # assume a dictionary is expected as replacement value
                self.logMsg("info", "  replacing ${" + var + "} with " + str(replacementValue))
                return (replacementValue, isDollarBrace)
            ee = var.find("]", bb)
            if ee == -1:
                self.add_error("Couldn't find ] for dictionary entry in replacement variable: " + var, moduleName, "---", "high")
                return (self.variableErrorReplacement + var + "}", isDollarBrace)
            vn = var[bb+1:ee]
            replacementValue = replacementValue.get(vn, self.variableErrorReplacement + var + "}#[" + vn + "]")
            if self.variableErrorReplacement[:1] in str(replacementValue):
                self.logMsg("debug", "Couldn't find a replacement (2) for: " + var + " in " + moduleName)
            if type(replacementValue) is list:
                replacementValue = str(replacementValue)
                self.logMsg("info", "  replacing ${" + var + "}[" + vn + "] with " + replacementValue)

        if type(replacementValue) is list:
            replacementValue = str(replacementValue)
            self.logMsg("info", "  replacing ${" + var + "} with " + replacementValue)

        return (replacementValue, isDollarBrace)

    # find deepest nested variable in given value
    def findVariable(self, value, shouldRecurse, isNested, previouslyFoundVar):
        # pass 1: if unreplaceable, change $ to @
        # pass 2: if unreplaceable, change both $ & @ to !
        if type(value) is str:
            isDollarBrace = False
            b, e = self.findVariableDelineators(value, self.variableFind, "}")
            if b > -1:
                isDollarBrace = True
                if e == -1:
                    # problem
                    self.add_error("Matching close brace not found: " + value, "---", "---", "high")
                    return None
            elif isNested:
                # only look for brackets if nested inside ${}
                b, e = self.findVariableDelineators(value, "[", "]")
                if b == -1:
                    return previouslyFoundVar
                if e == -1:
                    # problem
                    self.add_error("Matching close square bracket not found: " + value, "---", "---", "high")
                    return None
            else:
                return previouslyFoundVar
            foundVar = (value[b:e], b, e)
            # recursively find variable to find brackets nested inside braces
            newSearchValue = foundVar[0]
            if isDollarBrace:
                newSearchValue = newSearchValue[2:len(newSearchValue)-1]
            else:
                newSearchValue = newSearchValue[1:len(newSearchValue)-1]
                # adjust beginning & ending since nested inside previouslyFoundVar
                b += 2
                e += 2
                foundVar = (foundVar[0], b, e)
            if shouldRecurse:
                return self.findVariable(newSearchValue, True, True, foundVar)
            else:
                return foundVar
        return previouslyFoundVar

    def findVariableDelineators(self, value, open, close):
        b = value.rfind(open)
        if b == -1:
            return -1, 0
        v = value[b+1:]
        nested = 0
        for i, c in enumerate(v):
            if c == close:
                if nested == 0:
                    return b, b+i+2
                # just closed a nested variable
                nested -= 1
            if v[i:i+len(open)] == open or (len(open) == 2 and v[i:i+2] == self.variableErrorReplacement):
                # start of a nested variable
                nested += 1
        # error: matching close not found
        return 0, -1

    # find replacement value for given var in given moduleName
    def getReplacementValue(self, var, moduleName, dictToCopyFrom=None, tfDict=None):
        replacementValue = None
        if var.startswith('"') and var.endswith('"'):
            return var[1:len(var)-1], moduleName, True
        e = var.find("[")
        if e != -1:
            v = var[:e]
        else:
            v = var

        isHandledType = False
        notHandled = ["?", "==", "!=", ">", "<", ">=", "<=", "&&", "||", "!", "+", "-", "*", "/", "%"]
        moduleDict = self.modulesDict[moduleName]
        if var.startswith("var."):
            # conditional statements, boolean statements, and math are not currently handled
            if not any(x in var for x in notHandled):
                isHandledType = True
            v = v[4:]
            replacementValue = moduleDict[self.VARIABLE].get(v)
        elif var.startswith("local."):
            if not any(x in var for x in notHandled):
                isHandledType = True
            v = v[6:]
            replacementValue = moduleDict[self.LOCALS].get(v)
        elif var.startswith("module."):
            if not any(x in var for x in notHandled):
                isHandledType = True
            # variable is in a different module
            e = v.find(".", 7)
            if e == -1:
                self.add_error("Error Resolving module variable: " + var + "  expected ending '.' not found", moduleName, "---", "high")
            else:
                moduleName = v[7:e]
                md = self.getModule(moduleName, True, dictToCopyFrom, tfDict)
                moduleOutputDict = md[self.OUTPUT]
                e += 1
                remainingVar = v[e:]
                while remainingVar != "":
                    t = self.getNextLevel(remainingVar, ".")
                    moduleOutputDict = moduleOutputDict.get(t[0])
                    if moduleOutputDict is None:
                        self.logMsg("error", "Error resolving variable: " + v + "  variable not found in module (no module source available?) in " + moduleName)
                        return var, moduleName, True
                    remainingVar = t[1]
                if type(moduleOutputDict) is dict:
                    replacementValue = moduleOutputDict.get(self.VALUE, moduleOutputDict)
                else:
                    replacementValue = moduleOutputDict

        if type(replacementValue) is dict and len(replacementValue) == 0:
            replacementValue = None

        if replacementValue is None:
            replacementValue = self.variablesFromCommandLine.get(var, var)

        return replacementValue, moduleName, isHandledType

    def getPreviousLevel(self, var, separator):
        b = var.rfind(separator)
        if b == -1:
            b = len(var)
        return (var[:b], var[b+1:])

    def getNextLevel(self, var, separator):
        b = var.find(separator)
        if b == -1:
            b = len(var)
        return (var[:b], var[b+1:])

    # add given failure in given fileName
    def add_failure(self, failure, moduleName, fileName, severity):
        self.jsonOutput["failures"].append( self.getFailureMsg(severity, failure, moduleName, fileName) )

    # add given error in given fileName
    def add_error(self, error, moduleName, fileName, severity):
        if self.passNumber == 2 and self.shouldLogErrors:
            self.jsonOutput["errors"].append( self.getFailureMsg(severity, error, moduleName, fileName) )

    def getFailureMsg(self, severity, msg, moduleName, fileName):
        message = {}
        message["severity"] = severity
        message["message"] = msg
        message["moduleName"] = moduleName
        message["fileName"] = fileName
        return message

    def logMsg(self, type, msg):
        if self.passNumber == 2:
            if type == "error":
                logging.error(msg)
            elif type == "warning":
                logging.warning(msg)
            elif type == "info":
                logging.info(msg)
            elif type == "debug":
                logging.debug(msg)
