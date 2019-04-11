import unittest
import logging
import terraform_validate
from terraform_validate import TerraformResource


def getMsg(severity, msg, fileName, moduleName):
    return {'severity': severity, 'message': msg, 'moduleName': moduleName, 'fileName': fileName}


def createModule(p, parent, moduleName):
    d = {}
    d[p.PARENT] = parent
    d[p.IS_MODULE] = True
    d[p.MODULE_NAME] = moduleName
    d[p.VARIABLE] = {}
    d[p.LOCALS] = {}
    d[p.OUTPUT] = {}
    d[p.RESOURCE] = {}
    d[p.MODULE] = {}
    if parent is not None:
        parent[moduleName] = d
    return d


###############################################################
# assert helpers
###############################################################
def assertFailuresAndErrors(unittest, v, expectedFailures, expectedErrors):
    assertFailures( unittest, expectedFailures, v.preprocessor.jsonOutput["failures"] )
    assertErrors( unittest, expectedErrors, v.preprocessor.jsonOutput["errors"] )


def assertFailures(unittest, expectedFailures, actualFailures):
    unittest.assertEqual( len(expectedFailures), len(actualFailures), "number of expected failures doesn't match number of actual failures" )
    if len(expectedFailures) > 0:
        for expectedFailure, actualFailure in zip(expectedFailures, actualFailures):
            unittest.assertEqual( expectedFailure, actualFailure, "expected failure doesn't match actual failure")


def assertErrors(unittest, expectedErrors, actualErrors):
    unittest.assertEqual( len(expectedErrors), len(actualErrors), "number of expected errors doesn't match number of actual errors" )
    if len(expectedErrors) > 0:
        for expectedError, actualError in expectedErrors, actualErrors:
            unittest.assertEqual( expectedError, actualError, "expected error doesn't match actual error")


###############################################################
# resource helpers
###############################################################
def addResource(resources, name, type, config, fileName, moduleName):
    resources[name] = TerraformResource(type, name, config, fileName, moduleName)


###############################################################
# Preprocessor helpers/data
###############################################################
def getValidator(resources):
    jsonOutput = {
        "failures": [],
        "errors": []
    }
    v = terraform_validate.Validator()
    v.preprocessor = terraform_validate.PreProcessor(jsonOutput)
    terraform = {}
    terraform['resource'] = resources
    v.setTerraform(terraform)
    return v


def createHCLentry(p, parent, moduleName, isModule=True, fileName=None):
    d = {}
    if isModule:
        d[p.PARENT] = parent
        d[p.IS_MODULE] = True
        d[p.MODULE_NAME] = moduleName
    else:
        d[p.VARIABLE] = {}
        d[p.LOCALS] = {}
        d[p.OUTPUT] = {}
        d[p.RESOURCE] = {}
        d[p.MODULE] = {}
        d[p.FILE_NAME] = fileName
    if parent is not None:
        parent[moduleName] = d
    return d


moduleName = "10-root"
mainFileName = "C:\\DEV\\terraforms\\backends\\10-root\\main.tf"
resourceMyRoute = "myRoute"
resourceMyRouteValue = {'route_table_id': '${var.route_table_id}', 'destination_cidr_block': '${var.destination_cidr}', 'gateway_id': '${var.vgw_id}'}
localsEnv = "env"
localsEnvValue = "${var.environment}"
localsVpcType = "vpc_type"
localsVpcTypeValue = "analytics"
testVpcId = 'vpc-2'
localsEnvVpcId = "env_vpc_id"
localsEnvVpcIdValue = {'isbx': 'vpc-1', 'test': testVpcId, 'prod': 'vpc-3'}
localsVpcId = "vpc_id"
localsVpcIdValue = "${local.env_vpc_id[local.env]}"
localsSubmetNamePrefix = "subnet-name-prefix"
localsSubmetNamePrefixValue = "sf-${module.common.account_name}-${local.vpc_type}-${local.env}"

commonOutputAccountName = "account_name"
commonOutputAccountNameValue = "pcas"
testDomainName = 'pcas.test.ic1'
testIP = '234.567'
configOutput1 = "configOutput1"
configOutput2 = "configOutput2"
configOutput3 = "domain_name"
configOutput3Value = {'dev': 'pcas.dev.ic1', 'test': testDomainName, 'prod': 'pcas.prod.ic1'}
configVar1 = "ip"
configVar1Value = {'dev': '123.456', 'test': testIP, 'prod': '345.678'}
configLocal1 = "configLocal1"
configLocal1Value = "thisIsALocalValue"
configLocal2 = "configLocal2"
configLocal2Value = "${var." + configVar1 + "[var.environment]}"
output1 = "output1"
output1Value = "${module.config.yada[var.environment]}"
output2 = "output2"
output2Value = "output2Value"

varEnvironmentValue = "test"


def createHCL(p):
    root = createHCLentry(p, None, "root")
    modules = createHCLentry(p, root, "modules")
    common = createHCLentry(p, modules, "common")
    outputCommon = createHCLentry(p, common, "output.tf", False, "C:\\DEV\\terraforms\\modules\\common\\output.tf")
    outputCommon[p.OUTPUT][commonOutputAccountName] = {}
    outputCommon[p.OUTPUT][commonOutputAccountName][p.VALUE] = commonOutputAccountNameValue
    config = createHCLentry(p, modules, "config")
    outputConfig = createHCLentry(p, config, "output.tf", False, "C:\\DEV\\terraforms\\modules\\config\\output.tf")
    outputConfig[p.OUTPUT][configOutput1] = {}
    outputConfig[p.OUTPUT][configOutput1][p.VALUE] = configOutput1
    outputConfig[p.OUTPUT][configOutput2] = {}
    outputConfig[p.OUTPUT][configOutput2][p.VALUE] = configOutput2
    outputConfig[p.OUTPUT][configOutput3] = {}
    outputConfig[p.OUTPUT][configOutput3][p.VALUE] = configOutput3Value
    outputConfig[p.LOCALS][configLocal1] = configLocal1Value
    outputConfig[p.LOCALS][configLocal2] = configLocal2Value
    varConfig = createHCLentry(p, config, "vars.tf", False, "C:\\DEV\\terraforms\\modules\\config\\vars.tf")
    varConfig[p.VARIABLE][configVar1] = {"default": configVar1Value}
    private_gw = createHCLentry(p, modules, "private-gw")
    private_gw_vars = createHCLentry(p, private_gw, "vars.tf", False, "C:\\DEV\\terraforms\\modules\\private_gw\\vars.tf")
    private_gw_vars[p.VARIABLE]["aws_region"] = {}
    private_gw_vars[p.VARIABLE]["vpc_id"] = {"default": "none"}
    backends = createHCLentry(p, root, "backends")
    d = createHCLentry(p, backends, moduleName)
    backend = createHCLentry(p, d, "backend.tf", False, "C:\\DEV\\terraforms\\backends\\10-root\\backend.tf")
    backend[p.MODULE]["common"] = {}
    backend[p.MODULE]["common"][p.SOURCE] = "../../modules/common"
    backend[p.MODULE]["config"] = {}
    backend[p.MODULE]["config"][p.SOURCE] = "../../modules/config"
    backend[p.MODULE]["config"]["env"] = "${var.environment}"
    backend[p.LOCALS][localsEnv] = localsEnvValue
    env = createHCLentry(p, d, "env.tf", False, "C:\\DEV\\terraforms\\backends\\10-root\\env.tf")
    env[p.LOCALS][localsVpcType] = localsVpcTypeValue
    env[p.LOCALS][localsEnvVpcId] = localsEnvVpcIdValue
    env[p.LOCALS][localsVpcId] = localsVpcIdValue
    env[p.LOCALS][localsSubmetNamePrefix] = localsSubmetNamePrefixValue
    main = createHCLentry(p, d, "main.tf", False, mainFileName)
    main[p.MODULE]["private-gw"] = {}
    main[p.MODULE]["private-gw"][p.SOURCE] = "../../modules/private-gw"
    main[p.MODULE]["private-gw"]["vpc_id"] = "${local.vpc_id}"
    main[p.MODULE]["private-gw"]["aws_region"] = "${module.common.region}"
    main[p.RESOURCE]["aws_route"] = {}
    main[p.RESOURCE]["aws_route"][resourceMyRoute] = resourceMyRouteValue
    output = createHCLentry(p, d, "output.tf", False, "C:\\DEV\\terraforms\\backends\\10-root\\output.tf")
    output[p.OUTPUT][output1] = {}
    output[p.OUTPUT][output1][p.VALUE] = output1Value
    output[p.OUTPUT][output2] = {}
    output[p.OUTPUT][output2][p.VALUE] = output2Value
    p.hclDict = root
    p.variablesFromCommandLine = {}
    p.variablesFromCommandLine["var.environment"] = varEnvironmentValue

    return d, moduleName


class TestValidator(unittest.TestCase):

    ###############################################################
    # property tests
    ###############################################################
    def test_get_terraform_tfproperties(self):
        # initialize
        v = getValidator({})
        terraformPropertyList = terraform_validate.TerraformPropertyList(v)
        # set up expected outputs
        expected = []
        # run test
        actual = terraformPropertyList.tfproperties()
        # asserts
        self.assertEqual(expected, actual, "expected tfproperties does not match actual tfproperties")

    def test_get_terraform_missing_property_ok(self):
        # initialize
        # initialize
        resourceName = 'resource'
        resourceType = 'aws_instance'
        propertyName = 'foo'
        moduleName = 'someModule'
        fileName = 'none.tf'
        resources = {}
        addResource(resources, resourceName, resourceType, {propertyName: {'device_name': 'myInstance', 'ebs_block_device': {'encrypted': False}}}, fileName, moduleName)
        v = getValidator(resources)
        # set up expected outputs
        expectedFailures = []
        expectedErrors = []
        # run test
        v.resources('aws_instance').property('xyz').property('encrypted').should_equal(True)
        # asserts
        assertFailuresAndErrors(self, v, expectedFailures, expectedErrors)

    def test_get_terraform_missing_property_failure(self):
        # initialize
        resourceName = 'resource'
        resourceType = 'aws_instance'
        propertyName = 'foo'
        moduleName = 'someModule'
        fileName = 'none.tf'
        resources = {}
        addResource(resources, resourceName, resourceType, {propertyName: {'device_name': 'myInstance', 'ebs_block_device': {'encrypted': False}}}, fileName, moduleName)
        v = getValidator(resources)
        v.error_if_property_missing()
        # set up expected outputs
        expectedFailures = []
        expectedFailures.append( getMsg("high", "[" + resourceType + "." + resourceName + "] should have property: 'xyz'", fileName, moduleName) )
        expectedErrors = []
        # run test
        v.resources('aws_instance').property('xyz').property('encrypted').should_equal(True)
        # asserts
        assertFailuresAndErrors(self, v, expectedFailures, expectedErrors)

    def test_get_terraform_property_that_exists(self):
        # initialize
        resourceName1 = 'foo'
        resourceType = 'aws_instance'
        propertyName = 'value'
        moduleName = 'someModule'
        fileName = 'none.tf'
        resources = {}
        addResource(resources, resourceName1, resourceType, {'value2': 3, propertyName: 2}, fileName, moduleName)
        resourceName2 = 'bar'
        addResource(resources, resourceName2, resourceType, {'value2': 2, propertyName: 1}, fileName, moduleName)
        v = getValidator(resources)
        # set up expected outputs
        expectedFailures = []
        expectedFailures.append( getMsg("high", "[" + resourceType + "." + resourceName1 + "." + propertyName + "] should be '1'. Is: '2'", fileName, moduleName) )
        expectedFailures.append( getMsg("high", "[" + resourceType + "." + resourceName2 + "." + propertyName + "] should be '2'. Is: '1'", fileName, moduleName) )
        expectedErrors = []
        # run test
        v.resources(resourceType).property(propertyName).should_equal(1)
        v.resources(resourceType).property(propertyName).should_equal(2)
        # asserts
        assertFailuresAndErrors(self, v, expectedFailures, expectedErrors)

    def test_get_terraform_property_should_not_equal_ok(self):
        # initialize
        resourceName = 'something'
        resourceType = 'aws_alb_listener'
        propertyName = 'protocol'
        moduleName = 'someModule'
        fileName = 'none.tf'
        resources = {}
        addResource(resources, resourceName, resourceType, {propertyName: 'hTTp'}, fileName, moduleName)
        v = getValidator(resources)
        # set up expected outputs
        expectedFailures = []
        expectedErrors = []
        # run test
        v.resources(resourceType).property(propertyName).should_not_equal('http')
        # asserts
        assertFailuresAndErrors(self, v, expectedFailures, expectedErrors)

    def test_get_terraform_property_should_not_equal_failure(self):
        # initialize
        resourceName = 'something'
        resourceType = 'aws_alb_listener'
        propertyName = 'protocol'
        moduleName = 'someModule'
        fileName = 'none.tf'
        resources = {}
        addResource(resources, resourceName, resourceType, {propertyName: 'http'}, fileName, moduleName)
        v = getValidator(resources)
        # set up expected outputs
        expectedFailures = []
        expectedFailures.append( getMsg("high", "[" + resourceType + "." + resourceName + "." + propertyName + "] should not be 'http'. Is: 'http'", fileName, moduleName) )
        expectedErrors = []
        # run test
        v.resources(resourceType).property(propertyName).should_not_equal('http')
        # asserts
        assertFailuresAndErrors(self, v, expectedFailures, expectedErrors)

    def test_get_terraform_property_should_not_equal_case_insensitive(self):
        # initialize
        resourceName = 'something'
        resourceType = 'aws_alb_listener'
        propertyName = 'protocol'
        moduleName = 'someModule'
        fileName = 'none.tf'
        resources = {}
        addResource(resources, resourceName, resourceType, {propertyName: 'hTTp'}, fileName, moduleName)
        v = getValidator(resources)
        # set up expected outputs
        expectedFailures = []
        expectedFailures.append( getMsg("high", "[" + resourceType + "." + resourceName + "." + propertyName + "] should not be 'http'. Is: 'hTTp'", fileName, moduleName) )
        expectedErrors = []
        # run test
        v.resources(resourceType).property(propertyName).should_not_equal_case_insensitive('http')
        # asserts
        assertFailuresAndErrors(self, v, expectedFailures, expectedErrors)

    def test_get_terraform_property_should_contain(self):
        # initialize
        resourceName = 'emr-master-ingress-self'
        resourceType = 'aws_security_group_rule'
        moduleName = 'someModule'
        fileName = 'none.tf'
        resources = {}
        addResource(resources, resourceName, resourceType, {'type': 'ingress', 'from_port': 0, 'to_port': 65535, 'protocol': 'tcp', 'cidr_blocks': ['0.0.0.0/0']}, fileName, moduleName)
        v = getValidator(resources)
        # set up expected outputs
        expectedFailures = []
        expectedFailures.append( getMsg("high", "[" + resourceType + "." + resourceName + ".cidr_blocks] '['0.0.0.0/0']' should contain '['xyz']'.", fileName, moduleName) )
        expectedErrors = []
        # run test
        v.resources('aws_security_group_rule').with_property('type', 'ingress').property('cidr_blocks').list_should_contain('xyz')
        # asserts
        assertFailuresAndErrors(self, v, expectedFailures, expectedErrors)

    def test_get_terraform_property_should_not_contain(self):
        # initialize
        resourceName = 'emr-master-ingress-self'
        resourceType = 'aws_security_group_rule'
        moduleName = 'someModule'
        fileName = 'none.tf'
        resources = {}
        addResource(resources, resourceName, resourceType, {'type': 'ingress', 'from_port': 0, 'to_port': 65535, 'protocol': 'tcp', 'cidr_blocks': ['0.0.0.0/0']}, fileName, moduleName)
        v = getValidator(resources)
        # set up expected outputs
        expectedFailures = []
        expectedFailures.append( getMsg("high", "[" + resourceType + "." + resourceName + ".cidr_blocks] '['0.0.0.0/0']' should not contain '['0.0.0.0/0']'.", fileName, moduleName) )
        expectedErrors = []
        # run test
        v.resources(resourceType).with_property('type', 'ingress').property('cidr_blocks').list_should_not_contain('0.0.0.0/0')
        # asserts
        assertFailuresAndErrors(self, v, expectedFailures, expectedErrors)

    def test_get_terraform_property_should_have_properties(self):
        # initialize
        resourceName = 'myS3bucket'
        resourceType = 'aws_s3_bucket'
        propertyName = 'myProperty'
        moduleName = 'someModule'
        fileName = 'none.tf'
        resources = {}
        addResource(resources, resourceName, resourceType, { propertyName: {'yadayadayada': 'aws:kms'}}, fileName, moduleName)
        v = getValidator(resources)
        # set up expected outputs
        expectedFailures = []
        expectedFailures.append( getMsg("high", "[" + resourceType + "." + resourceName + "." + propertyName + "] should have property: 'server_side_encryption_configuration'", fileName, moduleName) )
        expectedErrors = []
        # run test
        v.resources(resourceType).property(propertyName).should_have_properties('server_side_encryption_configuration')
        # asserts
        assertFailuresAndErrors(self, v, expectedFailures, expectedErrors)

    def test_get_terraform_property_should_not_have_properties(self):
        # initialize
        resourceName = 'myS3bucket'
        resourceType = 'aws_s3_bucket'
        propertyName = 'myProperty'
        moduleName = 'someModule'
        fileName = 'none.tf'
        resources = {}
        addResource(resources, resourceName, resourceType, { propertyName: {'yadayadayada': 'aws:kms'}}, fileName, moduleName)
        v = getValidator(resources)
        # set up expected outputs
        expectedFailures = []
        expectedFailures.append( getMsg("high", "[" + resourceType + "." + resourceName + "." + propertyName + "] should not have property: 'yadayadayada'", fileName, moduleName) )
        expectedErrors = []
        # run test
        v.resources(resourceType).property(propertyName).should_not_have_properties('yadayadayada')
        # asserts
        assertFailuresAndErrors(self, v, expectedFailures, expectedErrors)

    def test_get_terraform_property_find_property(self):
        # initialize
        resourceName = 'myS3bucket'
        resourceType = 'aws_s3_bucket'
        propertyName = 'myProperty'
        moduleName = 'someModule'
        fileName = 'none.tf'
        resources = {}
        addResource(resources, resourceName, resourceType, {propertyName: {'somePropery': 123, 'yadayadayada': 'aws:kms'}}, fileName, moduleName)
        v = getValidator(resources)
        # set up expected outputs
        expected = terraform_validate.TerraformProperty(resourceType, resourceName + "." + propertyName, "yadayadayada", "aws:kms", moduleName, fileName)
        # run test
        actualList = v.resources(resourceType).property(propertyName).find_property('yadayadayada')
        # asserts
        self.assertEqual( 1, len(actualList.properties))
        actual = actualList.properties[0]
        self.assertEqual( expected.property_name, actual.property_name, "expected property_name doesn't match actual property_name")
        self.assertEqual( expected.property_value, actual.property_value, "expected property_value doesn't match actual property_value")
        self.assertEqual( expected.resource_name, actual.resource_name, "expected resource_name doesn't match actual resource_name")
        self.assertEqual( expected.resource_type, actual.resource_type, "expected resource_type doesn't match actual resource_type")

    def test_get_terraform_property_should_match_regex_doesMatch(self):
        # initialize
        resourceName = 'foo'
        resourceType = 'aws_instance'
        propertyName1 = 'device_name'
        propertyName2 = 'ebs_block_device'
        propertyName3 = 'xyz'
        moduleName = 'someModule'
        fileName = 'none.tf'
        resources = {}
        addResource(resources, resourceName, resourceType, {propertyName1: 'myInstance'}, fileName, moduleName)
        addResource(resources, resourceName, resourceType, {propertyName2: {propertyName3: '{"something":"value"}'}}, fileName, moduleName)
        regex = '{"something":"value"}'
        v = getValidator(resources)
        # set up expected outputs
        expectedFailures = []
        expectedErrors = []
        # run test
        v.resources(resourceType).property(propertyName2).property(propertyName3).should_match_regex(regex)
        # asserts
        assertFailuresAndErrors(self, v, expectedFailures, expectedErrors)

    def test_get_terraform_property_should_match_regex_noMatch(self):
        # initialize
        resourceName = 'foo'
        resourceType = 'aws_instance'
        propertyName1 = 'device_name'
        propertyName2 = 'ebs_block_device'
        propertyName3 = 'xyz'
        moduleName = 'someModule'
        fileName = 'none.tf'
        resources = {}
        addResource(resources, resourceName, resourceType, {propertyName1: 'myInstance'}, fileName, moduleName)
        addResource(resources, resourceName, resourceType, {propertyName2: {propertyName3: '{"something":"value"}'}}, fileName, moduleName)
        regex = 'xyz'
        v = getValidator(resources)
        # set up expected outputs
        expectedFailures = []
        expectedFailures.append( getMsg("high", "[" + resourceType + "." + resourceName + "." + propertyName2 + "." + propertyName3 + "] should match regex 'xyz'", fileName, moduleName) )
        expectedErrors = []
        # run test
        v.resources(resourceType).property(propertyName2).property(propertyName3).should_match_regex(regex)
        # asserts
        assertFailuresAndErrors(self, v, expectedFailures, expectedErrors)

    def test_get_terraform_property_should_contain_valid_json_isValid(self):
        # initialize
        resourceName = 'foo'
        resourceType = 'aws_instance'
        propertyName1 = 'device_name'
        propertyName2 = 'ebs_block_device'
        propertyName3 = 'xyz'
        moduleName = 'someModule'
        fileName = 'none.tf'
        resources = {}
        addResource(resources, resourceName, resourceType, {propertyName1: 'myInstance'}, fileName, moduleName)
        addResource(resources, resourceName, resourceType, {propertyName2: {propertyName3: '{"something":"value"}'}}, fileName, moduleName)
        v = getValidator(resources)
        # set up expected outputs
        expectedFailures = []
        expectedErrors = []
        # run test
        v.resources(resourceType).property(propertyName2).property(propertyName3).should_contain_valid_json()
        # asserts
        assertFailuresAndErrors(self, v, expectedFailures, expectedErrors)

    def test_get_terraform_property_should_contain_valid_json_notValid(self):
        # initialize
        resourceName = 'foo'
        resourceType = 'aws_instance'
        propertyName1 = 'device_name'
        propertyName2 = 'ebs_block_device'
        propertyName3 = 'xyz'
        moduleName = 'someModule'
        fileName = 'none.tf'
        resources = {}
        addResource(resources, resourceName, resourceType, {propertyName1: 'myInstance'}, fileName, moduleName)
        addResource(resources, resourceName, resourceType, {propertyName2: {propertyName3: '{"something":"value"'}}, fileName, moduleName)
        v = getValidator(resources)
        # set up expected outputs
        expectedFailures = []
        expectedFailures.append( getMsg("high", "[" + resourceType + "." + resourceName + "." + propertyName2 + "." + propertyName3 + "] is not valid json", fileName, moduleName) )
        expectedErrors = []
        # run test
        v.resources(resourceType).property(propertyName2).property(propertyName3).should_contain_valid_json()
        # asserts
        assertFailuresAndErrors(self, v, expectedFailures, expectedErrors)

    def test_get_terraform_missing_property_of_property_ok(self):
        # initialize
        resourceName = 'foo'
        resourceType = 'aws_instance'
        propertyName1 = 'device_name'
        propertyName2 = 'ebs_block_device'
        moduleName = 'someModule'
        fileName = 'none.tf'
        resources = {}
        addResource(resources, resourceName, resourceType, {propertyName1: 'myInstance'}, fileName, moduleName)
        addResource(resources, resourceName, resourceType, {propertyName2: {'encrypted': False}}, fileName, moduleName)
        v = getValidator(resources)
        # set up expected outputs
        expectedFailures = []
        expectedErrors = []
        # run test
        v.resources(resourceType).property(propertyName2).property('xyz').should_equal(True)
        # asserts
        assertFailuresAndErrors(self, v, expectedFailures, expectedErrors)

    def test_get_terraform_missing_property_of_property_failure(self):
        resourceName = 'foo'
        resourceType = 'aws_instance'
        propertyName1 = 'device_name'
        propertyName2 = 'ebs_block_device'
        moduleName = 'someModule'
        fileName = 'none.tf'
        resources = {}
        addResource(resources, resourceName, resourceType, {propertyName1: 'myInstance'}, fileName, moduleName)
        addResource(resources, resourceName, resourceType, {propertyName2: {'encrypted': False}}, fileName, moduleName)
        v = getValidator(resources)
        v.error_if_property_missing()
        # set up expected outputs
        expectedFailures = []
        expectedFailures.append( getMsg("high", "[" + resourceType + "." + resourceName + "." + propertyName2 + "] should have property: 'xyz'", fileName, moduleName) )
        expectedErrors = []
        # run test
        v.resources(resourceType).property(propertyName2).property('xyz').should_equal(True)
        # asserts
        assertFailuresAndErrors(self, v, expectedFailures, expectedErrors)

    def test_get_terraform_property_of_property_should_equal(self):
        # initialize
        resourceName = 'foo'
        resourceType = 'aws_instance'
        propertyName1 = 'device_name'
        propertyName2 = 'ebs_block_device'
        propertyName3 = 'encrypted'
        moduleName = 'someModule'
        fileName = 'none.tf'
        resources = {}
        addResource(resources, resourceName, resourceType, {propertyName1: 'myInstance'}, fileName, moduleName)
        addResource(resources, resourceName, resourceType, {propertyName2: {propertyName3: False}}, fileName, moduleName)
        v = getValidator(resources)
        v.error_if_property_missing()
        # set up expected outputs
        expectedFailures = []
        expectedFailures.append( getMsg("high", "[" + resourceType + "." + resourceName + "." + propertyName2 + "." + propertyName3 + "] should be 'True'. Is: 'False'", fileName, moduleName) )
        expectedErrors = []
        # run test
        v.resources(resourceType).property(propertyName2).property(propertyName3).should_equal(True)
        # asserts
        assertFailuresAndErrors(self, v, expectedFailures, expectedErrors)

    def test_get_terraform_property_of_property_should_equal_case_insensitive(self):
        # initialize
        resourceName = 'foo'
        resourceType = 'aws_instance'
        propertyName1 = 'device_name'
        propertyName2 = 'ebs_block_device'
        propertyName3 = 'encrypted'
        moduleName = 'someModule'
        fileName = 'none.tf'
        resources = {}
        addResource(resources, resourceName, resourceType, {propertyName1: 'myInstance'}, fileName, moduleName)
        addResource(resources, resourceName, resourceType, {propertyName2: {propertyName3: 'yada'}}, fileName, moduleName)
        v = getValidator(resources)
        v.error_if_property_missing()
        # set up expected outputs
        expectedFailures = []
        expectedErrors = []
        # run test
        v.resources(resourceType).property(propertyName2).property(propertyName3).should_equal_case_insensitive('yADa')
        # asserts
        assertFailuresAndErrors(self, v, expectedFailures, expectedErrors)

    def test_get_all_resources(self):
        # initialize
        resourceName1 = 'foo'
        resourceType1 = 'aws_instance'
        propertyName = 'value'
        resourceName2 = 'bar'
        resourceType2 = 'aws_rds_instance'
        moduleName = 'someModule'
        fileName = 'none.tf'
        resources = {}
        addResource(resources, resourceName1, resourceType1, {propertyName: 1}, fileName, moduleName)
        addResource(resources, resourceName2, resourceType2, {propertyName: 1}, fileName, moduleName)
        v = getValidator(resources)
        a = v.resources(".*").property(propertyName)
        self.assertEqual(len(a.properties), 2)

    def test_get_all_aws_resources(self):
        resourceName1 = 'foo'
        resourceType1 = 'aws_instance'
        propertyName = 'value'
        resourceName2 = 'bar'
        resourceType2 = 'azure_rds_instance'
        moduleName = 'someModule'
        fileName = 'none.tf'
        resources = {}
        addResource(resources, resourceName1, resourceType1, {propertyName: 1}, fileName, moduleName)
        addResource(resources, resourceName2, resourceType2, {propertyName: 1}, fileName, moduleName)
        v = getValidator(resources)
        a = v.resources("aws_.*").property('value')
        self.assertEqual(len(a.properties), 1)

    ###############################################################
    # resource tests
    ###############################################################
    def test_get_terraform_resource_find_property(self):
        # initialize
        resourceName = 'foo'
        resourceType = 'aws_s3_bucket'
        propertyName = "yadayadayada"
        moduleName = 'someModule'
        fileName = 'none.tf'
        resources = {}
        addResource(resources, resourceName, resourceType, {'somePropery': 123, propertyName: 'aws:kms'}, fileName, moduleName)
        v = getValidator(resources)
        # set up expected outputs
        expected = terraform_validate.TerraformProperty(resourceType, resourceName, propertyName, "aws:kms", moduleName, fileName)
        # run test
        actualList = v.resources(resourceType).find_property(propertyName)
        # asserts
        self.assertEqual( 1, len(actualList.properties))
        actual = actualList.properties[0]
        self.assertEqual( expected.property_name, actual.property_name, "expected property_name doesn't match actual property_name")
        self.assertEqual( expected.property_value, actual.property_value, "expected property_value doesn't match actual property_value")
        self.assertEqual( expected.resource_name, actual.resource_name, "expected resource_name doesn't match actual resource_name")
        self.assertEqual( expected.resource_type, actual.resource_type, "expected resource_type doesn't match actual resource_type")

    def test_resources_doesnt_exist(self):
        # initialize
        resourceName = 'someName'
        resourceType = 'aws_instance'
        moduleName = 'someModule'
        fileName = 'none.tf'
        resources = {}
        addResource(resources, resourceName, resourceType, {'foo': {'value2': 2, 'value': 1}, 'bar': {'value2': 2, 'value': 1}}, fileName, moduleName)
        v = getValidator(resources)
        # set up expected outputs
        expected = []
        # run test
        actual = v.resources('aws_rds')
        # asserts
        self.assertEqual(actual.resource_list, expected)

    def test_resources_should_not_existt(self):
        # initialize
        resourceName = 'someName'
        resourceType = 'aws_iam_user_login_profile'
        moduleName = 'someModule'
        fileName = 'none.tf'
        resources = {}
        addResource(resources, resourceName, resourceType, {'foo': 'bar'}, fileName, moduleName)
        v = getValidator(resources)
        # set up expected outputs
        expectedFailures = []
        expectedFailures.append( getMsg("high", "[" + resourceType + "] should not exist. Found in resource named " + resourceName, fileName, moduleName) )
        expectedErrors = []
        # run test
        v.resources(resourceType).should_not_exist()
        # asserts
        assertFailuresAndErrors(self, v, expectedFailures, expectedErrors)

    def test_get_terraform_resource_should_have_properties(self):
        # initialize
        resourceName = 'myS3bucket'
        resourceType = 'aws_s3_bucket'
        moduleName = 'someModule'
        fileName = 'none.tf'
        resources = {}
        addResource(resources, resourceName, resourceType, {'yadayadayada': 'aws:kms'}, fileName, moduleName)
        v = getValidator(resources)
        # set up expected outputs
        expectedFailures = []
        expectedFailures.append( getMsg("high", "[" + resourceType + "." + resourceName + "] should have property: 'server_side_encryption_configuration'", fileName, moduleName) )
        expectedErrors = []
        # run test
        v.resources(resourceType).should_have_properties('server_side_encryption_configuration')
        # asserts
        assertFailuresAndErrors(self, v, expectedFailures, expectedErrors)

    def test_get_terraform_resource_should_not_have_properties(self):
        # initialize
        resourceName = 'myS3bucket'
        resourceType = 'aws_s3_bucket'
        propertyName = 'yadayadayada'
        moduleName = 'someModule'
        fileName = 'none.tf'
        resources = {}
        addResource(resources, resourceName, resourceType, {propertyName: 'aws:kms'}, fileName, moduleName)
        v = getValidator(resources)
        # set up expected outputs
        expectedFailures = []
        expectedFailures.append( getMsg("high", "[" + resourceType + "." + resourceName + "] should not have property: '" + propertyName + "'", fileName, moduleName) )
        expectedErrors = []
        # run test
        v.resources(resourceType).should_not_have_properties(propertyName)
        # asserts
        assertFailuresAndErrors(self, v, expectedFailures, expectedErrors)

    def test_get_terraform_resource_name_should_match_regex_doesMatch(self):
        # initialize
        resourceName = 'foo'
        resourceType = 'aws_instance'
        moduleName = 'someModule'
        fileName = 'none.tf'
        resources = {}
        addResource(resources, resourceName, resourceType, 123, fileName, moduleName)
        v = getValidator(resources)
        regex = 'foo'
        # set up expected outputs
        expectedFailures = []
        expectedErrors = []
        # run test
        v.resources(resourceType).name_should_match_regex(regex)
        # asserts
        assertFailuresAndErrors(self, v, expectedFailures, expectedErrors)

    def test_get_terraform_resource_name_should_match_regex_noMatch(self):
        # initialize
        resourceName = 'foo'
        resourceType = 'aws_instance'
        moduleName = 'someModule'
        fileName = 'none.tf'
        resources = {}
        addResource(resources, resourceName, resourceType, 123, fileName, moduleName)
        v = getValidator(resources)
        regex = 'xyz'
        # set up expected outputs
        expectedFailures = []
        expectedFailures.append( getMsg("high", "[" + resourceType + "." + resourceName + "] name should match regex: 'xyz'", fileName, moduleName) )
        expectedErrors = []
        # run test
        v.resources(resourceType).name_should_match_regex(regex)
        # asserts
        assertFailuresAndErrors(self, v, expectedFailures, expectedErrors)

    ###############################################################
    # misc tests
    ###############################################################
    def test_matches_regex_is_true(self):
        v = getValidator("{}")
        a = v.matches_regex_pattern('abc_123', '^abc_123$')
        self.assertTrue(a)

    def test_matches_multiline_regex_is_true(self):
        v = getValidator("{}")
        a = v.matches_regex_pattern('abc_\n123', '^abc_.123$')
        self.assertTrue(a)

    def test_matches_regex_is_false(self):
        v = getValidator("{}")
        a = v.matches_regex_pattern('abc_123', '^abc_321$')
        self.assertFalse(a)

    def test_matches_regex_whole_string_only(self):
        v = getValidator("{}")
        a = v.matches_regex_pattern('abc_123', 'abc')
        self.assertFalse(a)

    def test_bool_to_str(self):
        a = terraform_validate.TerraformPropertyList(None)
        self.assertEqual(terraform_validate.TerraformPropertyList.bool2str(a, True), "True")
        self.assertEqual(terraform_validate.TerraformPropertyList.bool2str(a, "True"), "True")
        self.assertEqual(terraform_validate.TerraformPropertyList.bool2str(a, False), "False")
        self.assertEqual(terraform_validate.TerraformPropertyList.bool2str(a, "False"), "False")

    ###############################################################
    # Preprocessor tests
    ###############################################################
    def test_getAllModules(self):
        # initialize
        jsonOutput = {
            "failures": [],
            "errors": []
        }
        p = terraform_validate.PreProcessor(jsonOutput)
        d, moduleName = createHCL(p)
        # run test
        p.getAllModules(p.hclDict, False)
        # asserts
        self.assertEqual(6, len(p.modulesDict))

        module = p.modulesDict["modules"]
        self.assertEqual(0, len(module[p.VARIABLE]))
        self.assertEqual(0, len(module[p.LOCALS]))
        self.assertEqual(0, len(module[p.OUTPUT]))
        self.assertEqual(0, len(module[p.RESOURCE]))

        module = p.modulesDict["common"]
        self.assertEqual(0, len(module[p.VARIABLE]))
        self.assertEqual(0, len(module[p.LOCALS]))
        self.assertEqual(1, len(module[p.OUTPUT]))
        self.assertEqual(commonOutputAccountNameValue, module[p.OUTPUT][commonOutputAccountName])
        self.assertEqual(0, len(module[p.RESOURCE]))

        module = p.modulesDict["config"]
        self.assertEqual(1, len(module[p.VARIABLE]))
        self.assertEqual(configVar1Value, module[p.VARIABLE][configVar1])
        self.assertEqual(2, len(module[p.LOCALS]))
        self.assertEqual(configLocal1Value, module[p.LOCALS][configLocal1])
        self.assertEqual(testIP, module[p.LOCALS][configLocal2])
        self.assertEqual(3, len(module[p.OUTPUT]))
        self.assertEqual(configOutput1, module[p.OUTPUT][configOutput1])
        self.assertEqual(configOutput2, module[p.OUTPUT][configOutput2])
        self.assertEqual(configOutput3Value, module[p.OUTPUT][configOutput3])
        self.assertEqual(0, len(module[p.RESOURCE]))

        module = p.modulesDict["private-gw"]
        self.assertEqual(1, len(module[p.VARIABLE]))
        self.assertEqual("none", module[p.VARIABLE]["vpc_id"])
        self.assertEqual(0, len(module[p.LOCALS]))
        self.assertEqual(0, len(module[p.OUTPUT]))
        self.assertEqual(0, len(module[p.RESOURCE]))

        module = p.modulesDict["backends"]
        self.assertEqual(0, len(module[p.VARIABLE]))
        self.assertEqual(0, len(module[p.LOCALS]))
        self.assertEqual(0, len(module[p.OUTPUT]))
        self.assertEqual(0, len(module[p.RESOURCE]))

        module = p.modulesDict["10-root"]
        self.assertEqual(4, len(module[p.VARIABLE]))
        self.assertEqual(commonOutputAccountNameValue, module[p.VARIABLE][commonOutputAccountName])
        self.assertEqual(configOutput1, module[p.VARIABLE][configOutput1])
        self.assertEqual(configOutput2, module[p.VARIABLE][configOutput2])
        self.assertEqual(configOutput3Value, module[p.VARIABLE][configOutput3])

        self.assertEqual(5, len(module[p.LOCALS]))
        self.assertEqual(varEnvironmentValue, module[p.LOCALS][localsEnv])
        self.assertEqual(localsVpcTypeValue, module[p.LOCALS][localsVpcType])
        self.assertEqual(localsEnvVpcIdValue, module[p.LOCALS][localsEnvVpcId])
        self.assertEqual(testVpcId, module[p.LOCALS][localsVpcId])
        self.assertEqual("sf-pcas-analytics-test", module[p.LOCALS][localsSubmetNamePrefix])

        self.assertEqual(2, len(module[p.OUTPUT]))
        self.assertEqual("@{module.config.yada[test]}", module[p.OUTPUT][output1])
        self.assertEqual(output2Value, module[p.OUTPUT][output2])

        self.assertEqual(1, len(module[p.RESOURCE]))
        actualResource = module[p.RESOURCE][resourceMyRoute]
        self.assertEqual(str(resourceMyRouteValue).replace('$', '@'), str(actualResource.config))
        self.assertEqual(mainFileName, actualResource.fileName)
        self.assertEqual(moduleName, actualResource.moduleName)
        self.assertEqual(resourceMyRoute, actualResource.name)

    def test_getModule(self):
        # initialize
        logging.basicConfig(level=logging.CRITICAL)
        jsonOutput = {
            "failures": [],
            "errors": []
        }
        p = terraform_validate.PreProcessor(jsonOutput)
        d, moduleName = createHCL(p)
        # run test
        actualModuleDict = p.getModule(moduleName)
        # asserts
        self.assertEqual(4, len(actualModuleDict[p.VARIABLE]))
        self.assertEqual(commonOutputAccountNameValue, actualModuleDict[p.VARIABLE][commonOutputAccountName])
        self.assertEqual(configOutput1, actualModuleDict[p.VARIABLE][configOutput1])
        self.assertEqual(configOutput2, actualModuleDict[p.VARIABLE][configOutput2])
        self.assertEqual(configOutput3Value, actualModuleDict[p.VARIABLE][configOutput3])

        self.assertEqual(5, len(actualModuleDict[p.LOCALS]))
        self.assertEqual(varEnvironmentValue, actualModuleDict[p.LOCALS][localsEnv])
        self.assertEqual(localsVpcTypeValue, actualModuleDict[p.LOCALS][localsVpcType])
        self.assertEqual(localsEnvVpcIdValue, actualModuleDict[p.LOCALS][localsEnvVpcId])
        self.assertEqual(testVpcId, actualModuleDict[p.LOCALS][localsVpcId])
        self.assertEqual("sf-pcas-analytics-test", actualModuleDict[p.LOCALS][localsSubmetNamePrefix])

        self.assertEqual(2, len(actualModuleDict[p.OUTPUT]))
        self.assertEqual("@{module.config.yada[test]}", actualModuleDict[p.OUTPUT][output1])
        self.assertEqual(output2Value, actualModuleDict[p.OUTPUT][output2])

        self.assertEqual(1, len(actualModuleDict[p.RESOURCE]))
        actualResource = actualModuleDict[p.RESOURCE][resourceMyRoute]
        self.assertEqual(str(resourceMyRouteValue).replace('$', '@'), str(actualResource.config))
        self.assertEqual(mainFileName, actualResource.fileName)
        self.assertEqual(moduleName, actualResource.moduleName)
        self.assertEqual(resourceMyRoute, actualResource.name)

        p.passNumber = 2

        # run test #2 (second pass)
        actualModuleDict = p.getModule(moduleName)
        # asserts
        self.assertEqual(4, len(actualModuleDict[p.VARIABLE]))
        self.assertEqual(commonOutputAccountNameValue, actualModuleDict[p.VARIABLE][commonOutputAccountName])
        self.assertEqual(configOutput1, actualModuleDict[p.VARIABLE][configOutput1])
        self.assertEqual(configOutput2, actualModuleDict[p.VARIABLE][configOutput2])
        self.assertEqual(configOutput3Value, actualModuleDict[p.VARIABLE][configOutput3])

        self.assertEqual(5, len(actualModuleDict[p.LOCALS]))
        self.assertEqual(varEnvironmentValue, actualModuleDict[p.LOCALS][localsEnv])
        self.assertEqual(localsVpcTypeValue, actualModuleDict[p.LOCALS][localsVpcType])
        self.assertEqual(localsEnvVpcIdValue, actualModuleDict[p.LOCALS][localsEnvVpcId])
        self.assertEqual(testVpcId, actualModuleDict[p.LOCALS][localsVpcId])
        self.assertEqual("sf-pcas-analytics-test", actualModuleDict[p.LOCALS][localsSubmetNamePrefix])

        self.assertEqual(2, len(actualModuleDict[p.OUTPUT]))
        self.assertEqual("@{module.config.yada[test]}", actualModuleDict[p.OUTPUT][output1])
        self.assertEqual(output2Value, actualModuleDict[p.OUTPUT][output2])

        self.assertEqual(1, len(actualModuleDict[p.RESOURCE]))
        actualResource = actualModuleDict[p.RESOURCE][resourceMyRoute]
        self.assertEqual(str(resourceMyRouteValue).replace('$', '@'), str(actualResource.config))
        self.assertEqual(mainFileName, actualResource.fileName)
        self.assertEqual(moduleName, actualResource.moduleName)
        self.assertEqual(resourceMyRoute, actualResource.name)

    def test_findModule(self):
        # initialize
        jsonOutput = {
            "failures": [],
            "errors": []
        }
        p = terraform_validate.PreProcessor(jsonOutput)
        d, moduleName = createHCL(p)
        # run test
        actualModuleDict = p.findModule(moduleName, p.hclDict)
        # asserts
        self.assertEqual(4, len(actualModuleDict[p.VARIABLE]))
        self.assertEqual(commonOutputAccountNameValue, actualModuleDict[p.VARIABLE][commonOutputAccountName])
        self.assertEqual(configOutput1, actualModuleDict[p.VARIABLE][configOutput1])
        self.assertEqual(configOutput2, actualModuleDict[p.VARIABLE][configOutput2])
        self.assertEqual(configOutput3Value, actualModuleDict[p.VARIABLE][configOutput3])

        self.assertEqual(5, len(actualModuleDict[p.LOCALS]))
        self.assertEqual(varEnvironmentValue, actualModuleDict[p.LOCALS][localsEnv])
        self.assertEqual(localsVpcTypeValue, actualModuleDict[p.LOCALS][localsVpcType])
        self.assertEqual(localsEnvVpcIdValue, actualModuleDict[p.LOCALS][localsEnvVpcId])
        self.assertEqual(testVpcId, actualModuleDict[p.LOCALS][localsVpcId])
        self.assertEqual("sf-pcas-analytics-test", actualModuleDict[p.LOCALS][localsSubmetNamePrefix])

        self.assertEqual(2, len(actualModuleDict[p.OUTPUT]))
        self.assertEqual("@{module.config.yada[test]}", actualModuleDict[p.OUTPUT][output1])
        self.assertEqual(output2Value, actualModuleDict[p.OUTPUT][output2])

        self.assertEqual(1, len(actualModuleDict[p.RESOURCE]))
        actualResource = actualModuleDict[p.RESOURCE][resourceMyRoute]
        self.assertEqual(str(resourceMyRouteValue).replace('$', '@'), str(actualResource.config))
        self.assertEqual(mainFileName, actualResource.fileName)
        self.assertEqual(moduleName, actualResource.moduleName)
        self.assertEqual(resourceMyRoute, actualResource.name)

    def test_findModule_withDictToCopyFrom(self):
        # initialize
        jsonOutput = {
            "failures": [],
            "errors": []
        }
        p = terraform_validate.PreProcessor(jsonOutput)
        d, moduleName = createHCL(p)
        moduleName = "config"
        dictToCopyFrom = d["backend.tf"]["module"]["config"]
        # run test
        actualModuleDict = p.findModule(moduleName, p.hclDict, dictToCopyFrom, d)
        # asserts
        self.assertEqual(2, len(actualModuleDict[p.VARIABLE]))
        self.assertEqual("test", actualModuleDict[p.VARIABLE]["env"])
        self.assertEqual(configVar1Value, actualModuleDict[p.VARIABLE][configVar1])

        self.assertEqual(2, len(actualModuleDict[p.LOCALS]))
        self.assertEqual(configLocal1Value, actualModuleDict[p.LOCALS][configLocal1])
        self.assertEqual(testIP, actualModuleDict[p.LOCALS][configLocal2])

        self.assertEqual(3, len(actualModuleDict[p.OUTPUT]))
        self.assertEqual(configOutput1, actualModuleDict[p.OUTPUT][configOutput1])
        self.assertEqual(configOutput2, actualModuleDict[p.OUTPUT][configOutput2])
        self.assertEqual(configOutput3Value, actualModuleDict[p.OUTPUT][configOutput3])

        self.assertEqual(0, len(actualModuleDict[p.RESOURCE]))

    def test_loadModule(self):
        # initialize
        jsonOutput = {
            "failures": [],
            "errors": []
        }
        p = terraform_validate.PreProcessor(jsonOutput)
        d, moduleName = createHCL(p)
        dictToCopyFrom = d["main.tf"]["module"]["private-gw"]
        # run test
        actualModuleDict = p.loadModule(moduleName, d, dictToCopyFrom)
        # asserts
        self.assertEqual(6, len(actualModuleDict[p.VARIABLE]))
        self.assertEqual("vpc-2", actualModuleDict[p.VARIABLE]["vpc_id"])
        self.assertEqual("@{module.common.region}", actualModuleDict[p.VARIABLE]["aws_region"])
        self.assertEqual(commonOutputAccountNameValue, actualModuleDict[p.VARIABLE][commonOutputAccountName])
        self.assertEqual(configOutput1, actualModuleDict[p.VARIABLE][configOutput1])
        self.assertEqual(configOutput2, actualModuleDict[p.VARIABLE][configOutput2])
        self.assertEqual(configOutput3Value, actualModuleDict[p.VARIABLE][configOutput3])

        self.assertEqual(5, len(actualModuleDict[p.LOCALS]))
        self.assertEqual(varEnvironmentValue, actualModuleDict[p.LOCALS][localsEnv])
        self.assertEqual(localsVpcTypeValue, actualModuleDict[p.LOCALS][localsVpcType])
        self.assertEqual(localsEnvVpcIdValue, actualModuleDict[p.LOCALS][localsEnvVpcId])
        self.assertEqual(testVpcId, actualModuleDict[p.LOCALS][localsVpcId])
        self.assertEqual("sf-pcas-analytics-test", actualModuleDict[p.LOCALS][localsSubmetNamePrefix])

        self.assertEqual(2, len(actualModuleDict[p.OUTPUT]))
        self.assertEqual("@{module.config.yada[test]}", actualModuleDict[p.OUTPUT][output1])
        self.assertEqual(output2Value, actualModuleDict[p.OUTPUT][output2])

        self.assertEqual(1, len(actualModuleDict[p.RESOURCE]))
        actualResource = actualModuleDict[p.RESOURCE][resourceMyRoute]
        self.assertEqual(str(resourceMyRouteValue).replace('$', '@'), str(actualResource.config))
        self.assertEqual(mainFileName, actualResource.fileName)
        self.assertEqual(moduleName, actualResource.moduleName)
        self.assertEqual(resourceMyRoute, actualResource.name)

    def test_loadModuleAttributes_nestedModule(self):
        # initialize
        jsonOutput = {
            "failures": [],
            "errors": []
        }
        p = terraform_validate.PreProcessor(jsonOutput)
        moduleName = "common"
        d = createHCLentry(p, None, moduleName)
        moduleDict = p.createModuleEntry("yada")
        tfDict = createHCLentry(p, None, "yada")
        # run test
        p.loadModuleAttributes(moduleName, d, moduleDict, tfDict)
        # asserts
        self.assertEqual(0, len(moduleDict[p.VARIABLE]))
        self.assertEqual(0, len(moduleDict[p.LOCALS]))
        self.assertEqual(0, len(moduleDict[p.OUTPUT]))
        self.assertEqual(0, len(moduleDict[p.RESOURCE]))

    def test_loadModuleAttributes_(self):
        # initialize
        jsonOutput = {
            "failures": [],
            "errors": []
        }
        p = terraform_validate.PreProcessor(jsonOutput)
        d, moduleName = createHCL(p)
        moduleDict = p.createModuleEntry(moduleName)
        # run test
        p.loadModuleAttributes(moduleName, d, moduleDict, None)
        # asserts
        self.assertEqual(4, len(moduleDict[p.VARIABLE]))
        self.assertEqual(commonOutputAccountNameValue, moduleDict[p.VARIABLE][commonOutputAccountName])
        self.assertEqual(configOutput1, moduleDict[p.VARIABLE][configOutput1])
        self.assertEqual(configOutput2, moduleDict[p.VARIABLE][configOutput2])
        self.assertEqual(configOutput3Value, moduleDict[p.VARIABLE][configOutput3])

        self.assertEqual(5, len(moduleDict[p.LOCALS]))
        self.assertEqual(localsEnvValue, moduleDict[p.LOCALS][localsEnv])
        self.assertEqual(localsVpcTypeValue, moduleDict[p.LOCALS][localsVpcType])
        self.assertEqual(localsEnvVpcIdValue, moduleDict[p.LOCALS][localsEnvVpcId])
        self.assertEqual(localsVpcIdValue, moduleDict[p.LOCALS][localsVpcId])
        self.assertEqual(localsSubmetNamePrefixValue, moduleDict[p.LOCALS][localsSubmetNamePrefix])

        self.assertEqual(2, len(moduleDict[p.OUTPUT]))
        self.assertEqual(output1Value, moduleDict[p.OUTPUT][output1])
        self.assertEqual(output2Value, moduleDict[p.OUTPUT][output2])

        self.assertEqual(1, len(moduleDict[p.RESOURCE]))
        actualResource = moduleDict[p.RESOURCE][resourceMyRoute]
        self.assertEqual(resourceMyRouteValue, actualResource.config)
        self.assertEqual(mainFileName, actualResource.fileName)
        self.assertEqual(moduleName, actualResource.moduleName)
        self.assertEqual(resourceMyRoute, actualResource.name)

    def test_getSourcePath_Found(self):
        # initialize
        jsonOutput = {
            "failures": [],
            "errors": []
        }
        p = terraform_validate.PreProcessor(jsonOutput)
        sourcePath = "../../modules/common"
        parameterDict = createHCLentry(p, None, "root")
        parameterDict[p.SOURCE] = sourcePath
        # run test
        actual = p.getSourcePath(parameterDict)
        # asserts
        self.assertEqual(sourcePath, actual)

    def test_getSourcePath_notFound(self):
        # initialize
        jsonOutput = {
            "failures": [],
            "errors": []
        }
        p = terraform_validate.PreProcessor(jsonOutput)
        parameterDict = createHCLentry(p, None, "root")
        # run test
        actual = p.getSourcePath(parameterDict)
        # asserts
        self.assertIsNone(actual)

    def test_getModuleDictFromSourcePath_Found(self):
        # initialize
        jsonOutput = {
            "failures": [],
            "errors": []
        }
        p = terraform_validate.PreProcessor(jsonOutput)
        root = createHCLentry(p, None, "root")
        modules = createHCLentry(p, root, "modules")
        common = createHCLentry(p, modules, "common")
        subRoot = createHCLentry(p, root, "subRoot")
        thisLevel = createHCLentry(p, subRoot, "thisLevel")
        sourcePath = "../../modules/common"
        # set up expected output
        expectedModuleName = common[p.MODULE_NAME]
        # run test
        actual = p.getModuleDictFromSourcePath(sourcePath, thisLevel)
        # asserts
        self.assertEqual(expectedModuleName, actual[p.MODULE_NAME])

    def test_getModuleDictFromSourcePath_notFound(self):
        # initialize
        jsonOutput = {
            "failures": [],
            "errors": []
        }
        p = terraform_validate.PreProcessor(jsonOutput)
        root = createHCLentry(p, None, "root")
        modules = createHCLentry(p, root, "modules")
        createHCLentry(p, modules, "common")
        subRoot = createHCLentry(p, root, "subRoot")
        thisLevel = createHCLentry(p, subRoot, "thisLevel")
        sourcePath = "../../modules/common/yada"
        # run test
        actual = p.getModuleDictFromSourcePath(sourcePath, thisLevel)
        # asserts
        self.assertFalse(actual)

    def test_resolveVariablesInModule(self):
        # initialize
        jsonOutput = {
            "failures": [],
            "errors": []
        }
        varName = "varName"
        localName = "localName"
        outputName = "outputName"
        resourceName = "resourceName"
        varValue = "${var." + varName + "}"
        localValue = "${var." + localName + "}"
        outputValue = "${var." + outputName + "}"
        resourceValue = "${var." + resourceName + "}"
        newVarValue = "newVarValue"
        newLocalValue = "newLocalValue"
        newOutputValue = "newOutputValue"
        newResourceValue = "newResourceValue"
        moduleName = "inputModuleName"
        p = terraform_validate.PreProcessor(jsonOutput)
        p.modulesDict = {}
        p.modulesDict[moduleName] = p.createModuleEntry(moduleName)
        p.modulesDict[moduleName][p.VARIABLE][varName] = newVarValue
        p.modulesDict[moduleName][p.VARIABLE][localName] = newLocalValue
        p.modulesDict[moduleName][p.VARIABLE][outputName] = newOutputValue
        p.modulesDict[moduleName][p.VARIABLE][resourceName] = newResourceValue
        moduleDict = {}
        moduleDict[p.VARIABLE] = {}
        moduleDict[p.LOCALS] = {}
        moduleDict[p.OUTPUT] = {}
        moduleDict[p.RESOURCE] = {}
        moduleDict[p.RESOURCE][resourceName] = {}
        moduleDict[p.VARIABLE][varName] = varValue
        moduleDict[p.LOCALS][localName] = localValue
        moduleDict[p.OUTPUT][outputName] = outputValue
        moduleDict[p.RESOURCE][resourceName] = TerraformResource("type", "name", resourceValue, "fileName", moduleName)
        # set up expected output
        expectedModuleDict = {}
        expectedModuleDict[p.VARIABLE] = {}
        expectedModuleDict[p.LOCALS] = {}
        expectedModuleDict[p.OUTPUT] = {}
        expectedModuleDict[p.RESOURCE] = {}
        expectedModuleDict[p.RESOURCE][resourceName] = {}
        expectedModuleDict[p.VARIABLE][varName] = newVarValue
        expectedModuleDict[p.LOCALS][localName] = newLocalValue
        expectedModuleDict[p.OUTPUT][outputName] = newOutputValue
        expectedModuleDict[p.RESOURCE][resourceName] = TerraformResource("type", "name", newResourceValue, "fileName", moduleName)
        # run test
        p.resolveVariablesInModule(moduleName, moduleDict)
        # asserts
        self.assertEqual(expectedModuleDict[p.VARIABLE], moduleDict[p.VARIABLE])
        self.assertEqual(expectedModuleDict[p.LOCALS], moduleDict[p.LOCALS])
        self.assertEqual(expectedModuleDict[p.OUTPUT], moduleDict[p.OUTPUT])
        self.assertEqual(expectedModuleDict[p.RESOURCE][resourceName].config, moduleDict[p.RESOURCE][resourceName].config)

    def test_resolveDictVariable(self):
        # initialize
        jsonOutput = {
            "failures": [],
            "errors": []
        }
        p = terraform_validate.PreProcessor(jsonOutput)
        newValue = "newValue"
        varName = "varName"
        anotherDict = {}
        anotherDict["key"] = "${var." + varName + "}"
        value = {}
        value["key1"] = "yada"
        value["key2"] = []
        value["key3"] = anotherDict
        moduleName = "inputModuleName"
        p.modulesDict = {}
        p.modulesDict[moduleName] = p.createModuleEntry(moduleName)
        p.modulesDict[moduleName][p.VARIABLE][varName] = newValue
        # set up expected output
        expectedDict = {}
        expectedDict["key"] = newValue
        expected = {}
        expected["key1"] = "yada"
        expected["key2"] = []
        expected["key3"] = expectedDict
        # run test
        actual = p.resolveDictVariable(value, moduleName)
        # asserts
        self.assertEqual(expected, actual)

    def test_resolveListVariable(self):
        # initialize
        jsonOutput = {
            "failures": [],
            "errors": []
        }
        p = terraform_validate.PreProcessor(jsonOutput)
        newValue = "newValue"
        varName = "varName"
        value = []
        anotherList = []
        anotherList.append("${var." + varName + "}")
        aDict = {}
        value.append("yada")
        value.append(anotherList)
        value.append(aDict)
        moduleName = "inputModuleName"
        p.modulesDict = {}
        p.modulesDict[moduleName] = p.createModuleEntry(moduleName)
        p.modulesDict[moduleName][p.VARIABLE][varName] = newValue
        # set up expected output
        expectedList = []
        expectedList.append(newValue)
        expected = []
        expected.append("yada")
        expected.append(expectedList)
        expected.append(aDict)
        # run test
        actual = p.resolveListVariable(value, moduleName)
        # asserts
        self.assertEqual(expected, actual)

    def test_isModule_False(self):
        # initialize
        jsonOutput = {
            "failures": [],
            "errors": []
        }
        p = terraform_validate.PreProcessor(jsonOutput)
        d = {}
        d["key1"] = "value1"
        d["key2"] = "value2"
        # run test
        actual = p.isModule(d)
        # asserts
        self.assertEqual(False, actual)

    def test_isModule_True(self):
        # initialize
        jsonOutput = {
            "failures": [],
            "errors": []
        }
        p = terraform_validate.PreProcessor(jsonOutput)
        d = {}
        d["key1"] = "value1"
        d[p.IS_MODULE] = True
        # run test
        actual = p.isModule(d)
        # asserts
        self.assertEqual(True, actual)

    def test_hasTerraform_False(self):
        # initialize
        jsonOutput = {
            "failures": [],
            "errors": []
        }
        p = terraform_validate.PreProcessor(jsonOutput)
        d = {}
        d["key1"] = "value1"
        d["key2"] = "value2"
        # run test
        actual = p.hasTerraform(d)
        # asserts
        self.assertEqual(False, actual)

    def test_hasTerraform_True(self):
        # initialize
        jsonOutput = {
            "failures": [],
            "errors": []
        }
        p = terraform_validate.PreProcessor(jsonOutput)
        d = {}
        d["key1"] = "value1"
        d["key2.TF"] = "value2"
        # run test
        actual = p.hasTerraform(d)
        # asserts
        self.assertEqual(True, actual)

    def test_resolveVariableLine_varNotFound(self):
        # initialize
        jsonOutput = {
            "failures": [],
            "errors": []
        }
        p = terraform_validate.PreProcessor(jsonOutput)
        varName = "varName"
        innerValue = "{var." + varName + "}"
        value = "$" + innerValue
        moduleName = "inputModuleName"
        p.modulesDict = {}
        p.modulesDict[moduleName] = p.createModuleEntry(moduleName)
        # set up expected output
        expected = "@" + innerValue
        # run test
        actual = p.resolveVariableLine(value, moduleName, True)
        # asserts
        self.assertEqual(expected, actual, "resolved variable line not as expected")

    def test_resolveVariableLine_simple(self):
        # initialize
        jsonOutput = {
            "failures": [],
            "errors": []
        }
        p = terraform_validate.PreProcessor(jsonOutput)
        newValue = "newValue"
        varName = "varName"
        value = "${var." + varName + "}"
        moduleName = "inputModuleName"
        p.modulesDict = {}
        p.modulesDict[moduleName] = p.createModuleEntry(moduleName)
        p.modulesDict[moduleName][p.VARIABLE][varName] = newValue
        # set up expected output
        expected = newValue
        # run test
        actual = p.resolveVariableLine(value, moduleName, True)
        # asserts
        self.assertEqual(expected, actual, "resolved variable line not as expected")

    def test_resolveVariableLine_complex(self):
        # initialize
        jsonOutput = {
            "failures": [],
            "errors": []
        }
        p = terraform_validate.PreProcessor(jsonOutput)
        nestedVarName = "nestedVarName"
        newValue = "newValue"
        varValue = {}
        varValue[nestedVarName] = newValue
        varName = "varName"
        value = "sf-core-${var." + varName + "[" + nestedVarName + "]}-yada"
        moduleName = "inputModuleName"
        p.modulesDict = {}
        p.modulesDict[moduleName] = p.createModuleEntry(moduleName)
        p.modulesDict[moduleName][p.VARIABLE][varName] = varValue
        # set up expected output
        expected = "sf-core-" + newValue + "-yada"
        # run test
        actual = p.resolveVariableLine(value, moduleName, True)
        # asserts
        self.assertEqual(expected, actual, "resolved variable line not as expected")

    def test_resolveVariable_varNotFound(self):
        # initialize
        jsonOutput = {
            "failures": [],
            "errors": []
        }
        p = terraform_validate.PreProcessor(jsonOutput)
        varName = "varName"
        innerValue = "{var." + varName + "}"
        value = "$" + innerValue
        moduleName = "inputModuleName"
        p.modulesDict = {}
        p.modulesDict[moduleName] = p.createModuleEntry(moduleName)
        # set up expected output
        expected = ("@" + innerValue, True)
        # run test
        actual = p.resolveVariable(value, moduleName, True)
        # asserts
        self.assertEqual(expected, actual, "resolved variable not as expected")

    def test_resolveVariable_nestedVarNotFound(self):
        # initialize
        jsonOutput = {
            "failures": [],
            "errors": []
        }
        p = terraform_validate.PreProcessor(jsonOutput)
        varName = "varName"
        expectedValue = "var." + varName
        value = "${yada[" + expectedValue + "]}"
        moduleName = "inputModuleName"
        p.modulesDict = {}
        p.modulesDict[moduleName] = p.createModuleEntry(moduleName)
        # set up expected output
        expected = (value, False)
        # run test
        actual = p.resolveVariable(value, moduleName, True)
        # asserts
        self.assertEqual(expected, actual, "resolved variable not as expected")

    def test_resolveVariable_simple(self):
        # initialize
        jsonOutput = {
            "failures": [],
            "errors": []
        }
        p = terraform_validate.PreProcessor(jsonOutput)
        newValue = "newValue"
        varName = "varName"
        value = "${var." + varName + "}"
        moduleName = "inputModuleName"
        p.modulesDict = {}
        p.modulesDict[moduleName] = p.createModuleEntry(moduleName)
        p.modulesDict[moduleName][p.VARIABLE][varName] = newValue
        # set up expected output
        expected = (newValue, True)
        # run test
        actual = p.resolveVariable(value, moduleName, True)
        # asserts
        self.assertEqual(expected, actual, "resolved variable not as expected")

    def test_resolveVariable_nested(self):
        # initialize
        jsonOutput = {
            "failures": [],
            "errors": []
        }
        p = terraform_validate.PreProcessor(jsonOutput)
        newValue = "newValue"
        varName = "varName"
        value = "${var.yada[var." + varName + "]}"
        moduleName = "inputModuleName"
        p.modulesDict = {}
        p.modulesDict[moduleName] = p.createModuleEntry(moduleName)
        p.modulesDict[moduleName][p.VARIABLE][varName] = newValue
        # set up expected output
        expected = ("${var.yada[" + newValue + "]}", False)
        # run test
        actual = p.resolveVariable(value, moduleName, True)
        # asserts
        self.assertEqual(expected, actual, "resolved variable not as expected")

    def test_resolveVariable_replacementIsDict(self):
        # initialize
        jsonOutput = {
            "failures": [],
            "errors": []
        }
        p = terraform_validate.PreProcessor(jsonOutput)
        nestedVarName = "nestedVarName"
        newValue = "newValue"
        varValue = {}
        varValue[nestedVarName] = newValue
        varName = "varName"
        value = "${var." + varName + "[" + nestedVarName + "]}"
        moduleName = "inputModuleName"
        p.modulesDict = {}
        p.modulesDict[moduleName] = p.createModuleEntry(moduleName)
        p.modulesDict[moduleName][p.VARIABLE][varName] = varValue
        # set up expected output
        expected = (newValue, True)
        # run test
        actual = p.resolveVariable(value, moduleName, False)
        # asserts
        self.assertEqual(expected, actual, "resolved variable not as expected")

    def test_findVariable_notString(self):
        # initialize
        jsonOutput = {
            "failures": [],
            "errors": []
        }
        p = terraform_validate.PreProcessor(jsonOutput)
        value = {}
        previouslyFoundVar = "previouslyFoundVar"
        # set up expected output
        expected = previouslyFoundVar
        # run test
        actual = p.findVariable(value, True, False, previouslyFoundVar)
        # asserts
        self.assertEqual(expected, actual, "found variable not as expected")

    def test_findVariable_noVariable(self):
        # initialize
        jsonOutput = {
            "failures": [],
            "errors": []
        }
        p = terraform_validate.PreProcessor(jsonOutput)
        value = "yadaYadaYada"
        previouslyFoundVar = "previouslyFoundVar"
        # set up expected output
        expected = previouslyFoundVar
        # run test
        actual = p.findVariable(value, True, False, previouslyFoundVar)
        # asserts
        self.assertEqual(expected, actual, "found variable not as expected")

    def test_findVariable_noCloseBrace(self):
        # initialize
        jsonOutput = {
            "failures": [],
            "errors": []
        }
        p = terraform_validate.PreProcessor(jsonOutput)
        value = "${yadaYadaYada"
        previouslyFoundVar = "previouslyFoundVar"
        # set up expected output
        expected = None
        # run test
        actual = p.findVariable(value, True, False, previouslyFoundVar)
        # asserts
        self.assertEqual(expected, actual, "found variable not as expected")

    def test_findVariable_noCloseSquareBracket(self):
        # initialize
        jsonOutput = {
            "failures": [],
            "errors": []
        }
        p = terraform_validate.PreProcessor(jsonOutput)
        value = "[yadaYadaYada"
        previouslyFoundVar = "previouslyFoundVar"
        # set up expected output
        expected = None
        # run test
        actual = p.findVariable(value, True, True, previouslyFoundVar)
        # asserts
        self.assertEqual(expected, actual, "found variable not as expected")

    def test_findVariable_simple(self):
        # initialize
        jsonOutput = {
            "failures": [],
            "errors": []
        }
        p = terraform_validate.PreProcessor(jsonOutput)
        value = "${yadaYadaYada}"
        previouslyFoundVar = "previouslyFoundVar"
        # set up expected output
        expected = (value, 0, 15)
        # run test
        actual = p.findVariable(value, True, False, previouslyFoundVar)
        # asserts
        self.assertEqual(expected, actual, "found variable not as expected")

    def test_findVariable_noRecurse(self):
        # initialize
        jsonOutput = {
            "failures": [],
            "errors": []
        }
        p = terraform_validate.PreProcessor(jsonOutput)
        value = "${yadaYadaYada[nested]}"
        previouslyFoundVar = "previouslyFoundVar"
        # set up expected output
        expected = (value, 0, 23)
        # run test
        actual = p.findVariable(value, False, False, previouslyFoundVar)
        # asserts
        self.assertEqual(expected, actual, "found variable not as expected")

    def test_findVariable_recurse(self):
        # initialize
        jsonOutput = {
            "failures": [],
            "errors": []
        }
        p = terraform_validate.PreProcessor(jsonOutput)
        nestedValue = "[nested]"
        value = "${yadaYadaYada" + nestedValue + "}"
        previouslyFoundVar = "previouslyFoundVar"
        # set up expected output
        expected = (nestedValue, 14, 22)
        # run test
        actual = p.findVariable(value, True, False, previouslyFoundVar)
        # asserts
        self.assertEqual(expected, actual, "found variable not as expected")

    def test_findVariableDelineators_openNotFound(self):
        # initialize
        jsonOutput = {
            "failures": [],
            "errors": []
        }
        p = terraform_validate.PreProcessor(jsonOutput)
        value = "yadaYadaYada"
        # set up expected output
        expected = -1, 0
        # run test
        actual = p.findVariableDelineators(value, "[", "]")
        # asserts
        self.assertEqual(expected, actual, "delineators not as expected")

    def test_findVariableDelineators_closeNotFound(self):
        # initialize
        jsonOutput = {
            "failures": [],
            "errors": []
        }
        p = terraform_validate.PreProcessor(jsonOutput)
        value = "${yadaYadaYada[}"
        # set up expected output
        expected = 0, -1
        # run test
        actual = p.findVariableDelineators(value, "[", "]")
        # asserts
        self.assertEqual(expected, actual, "delineators not as expected")

    def test_findVariableDelineators_simpleFound(self):
        # initialize
        jsonOutput = {
            "failures": [],
            "errors": []
        }
        p = terraform_validate.PreProcessor(jsonOutput)
        value = "${yadaYadaYada}"
        # set up expected output
        expected = 0, 15
        # run test
        actual = p.findVariableDelineators(value, "${", "}")
        # asserts
        self.assertEqual(expected, actual, "delineators not as expected")

    def test_findVariableDelineators_nestedFound(self):
        # initialize
        jsonOutput = {
            "failures": [],
            "errors": []
        }
        p = terraform_validate.PreProcessor(jsonOutput)
        value = "${yadaYadaYada[@{somethingElse}]}"
        # set up expected output
        expected = 0, 33
        # run test
        actual = p.findVariableDelineators(value, "${", "}")
        # asserts
        self.assertEqual(expected, actual, "delineators not as expected")

    def test_getReplacementValue_Literal(self):
        # initialize
        jsonOutput = {
            "failures": [],
            "errors": []
        }
        p = terraform_validate.PreProcessor(jsonOutput)
        newValue = "aVarValue"
        var = '"' + newValue + '"'
        moduleName = "aModuleName"
        # set up expected output
        expected = newValue, moduleName, True
        # run test
        actual = p.getReplacementValue(var, moduleName)
        # asserts
        self.assertEqual(expected, actual, "replacement value not as expected")

    def test_getReplacementValue_VarFound(self):
        # initialize
        jsonOutput = {
            "failures": [],
            "errors": []
        }
        p = terraform_validate.PreProcessor(jsonOutput)
        varName = "varName"
        var = 'var.' + varName
        moduleName = "aModuleName"
        newValue = "newValue"
        p.modulesDict = {}
        p.modulesDict[moduleName] = p.createModuleEntry(moduleName)
        p.modulesDict[moduleName][p.VARIABLE][varName] = newValue
        # set up expected output
        expected = newValue, moduleName, True
        # run test
        actual = p.getReplacementValue(var, moduleName)
        # asserts
        self.assertEqual(expected, actual, "replacement value not as expected")

    def test_getReplacementValue_VarNotFound(self):
        # initialize
        jsonOutput = {
            "failures": [],
            "errors": []
        }
        p = terraform_validate.PreProcessor(jsonOutput)
        varName = "varName"
        var = 'var.' + varName
        moduleName = "aModuleName"
        p.modulesDict = {}
        p.modulesDict[moduleName] = p.createModuleEntry(moduleName)
        p.modulesDict[moduleName][p.VARIABLE]["someOtherVar"] = "newValue"
        # set up expected output
        expected = var, moduleName, True
        # run test
        actual = p.getReplacementValue(var, moduleName)
        # asserts
        self.assertEqual(expected, actual, "replacement value not as expected")

    def test_getReplacementValue_CmdLineFound(self):
        # initialize
        jsonOutput = {
            "failures": [],
            "errors": []
        }
        p = terraform_validate.PreProcessor(jsonOutput)
        varName = "varName"
        var = 'var.' + varName
        moduleName = "aModuleName"
        newValue = "newValueFromCmdLine"
        p.modulesDict = {}
        p.modulesDict[moduleName] = p.createModuleEntry(moduleName)
        p.variablesFromCommandLine = {}
        p.variablesFromCommandLine[var] = newValue
        # set up expected output
        expected = newValue, moduleName, True
        # run test
        actual = p.getReplacementValue(var, moduleName)
        # asserts
        self.assertEqual(expected, actual, "replacement value not as expected")

    def test_getReplacementValue_LocalFound(self):
        # initialize
        jsonOutput = {
            "failures": [],
            "errors": []
        }
        p = terraform_validate.PreProcessor(jsonOutput)
        varName = "varName"
        var = 'local.' + varName
        moduleName = "aModuleName"
        newValue = "newValue"
        p.modulesDict = {}
        p.modulesDict[moduleName] = p.createModuleEntry(moduleName)
        p.modulesDict[moduleName][p.LOCALS][varName] = newValue
        # set up expected output
        expected = newValue, moduleName, True
        # run test
        actual = p.getReplacementValue(var, moduleName)
        # asserts
        self.assertEqual(expected, actual, "replacement value not as expected")

    def test_getReplacementValue_ModuleStringFound(self):
        # initialize
        jsonOutput = {
            "failures": [],
            "errors": []
        }
        p = terraform_validate.PreProcessor(jsonOutput)
        inputModuleName = "aModuleName"
        moduleName = "anotherModuleName"
        varName = "varName"
        var = 'module.' + moduleName + "." + varName
        newValue = "newValue"
        p.modulesDict = {}
        p.modulesDict[inputModuleName] = p.createModuleEntry(inputModuleName)
        p.modulesDict[moduleName] = p.createModuleEntry(moduleName)
        p.modulesDict[moduleName][p.OUTPUT][varName] = newValue
        # set up expected output
        expected = newValue, moduleName, True
        # run test
        actual = p.getReplacementValue(var, inputModuleName)
        # asserts
        self.assertEqual(expected, actual, "replacement value not as expected")

    def test_getReplacementValue_ModuleDictFound(self):
        # initialize
        jsonOutput = {
            "failures": [],
            "errors": []
        }
        p = terraform_validate.PreProcessor(jsonOutput)
        inputModuleName = "aModuleName"
        moduleName = "anotherModuleName"
        varName = "varName"
        newValue = "newValue"
        newValueDict = {}
        newValueDict[p.VALUE] = newValue
        var = 'module.' + moduleName + "." + varName
        p.modulesDict = {}
        p.modulesDict[inputModuleName] = p.createModuleEntry(inputModuleName)
        p.modulesDict[moduleName] = p.createModuleEntry(moduleName)
        p.modulesDict[moduleName][p.OUTPUT][varName] = newValueDict
        # set up expected output
        expected = newValue, moduleName, True
        # run test
        actual = p.getReplacementValue(var, inputModuleName)
        # asserts
        self.assertEqual(expected, actual, "replacement value not as expected")

    def test_getReplacementValue_ModuleDictEmpty(self):
        # initialize
        jsonOutput = {
            "failures": [],
            "errors": []
        }
        p = terraform_validate.PreProcessor(jsonOutput)
        inputModuleName = "aModuleName"
        moduleName = "anotherModuleName"
        varName = "varName"
        var = 'module.' + moduleName + "." + varName
        p.modulesDict = {}
        p.modulesDict[inputModuleName] = p.createModuleEntry(inputModuleName)
        p.modulesDict[moduleName] = p.createModuleEntry(moduleName)
        p.modulesDict[moduleName][p.OUTPUT][varName] = {}
        # set up expected output
        expected = var, moduleName, True
        # run test
        actual = p.getReplacementValue(var, inputModuleName)
        # asserts
        self.assertEqual(expected, actual, "replacement value not as expected")

    def test_getPreviousLevel_notFound(self):
        # initialize
        jsonOutput = {
            "failures": [],
            "errors": []
        }
        p = terraform_validate.PreProcessor(jsonOutput)
        var = "dir"
        separator = "/"
        # set up expected output
        expected = "dir", ""
        # run test
        actual = p.getPreviousLevel(var, separator)
        # asserts
        self.assertEqual(expected, actual, "level not as expected")

    def test_getgetPreviousLevel_found(self):
        # initialize
        jsonOutput = {
            "failures": [],
            "errors": []
        }
        p = terraform_validate.PreProcessor(jsonOutput)
        var = "level1/level2/level3"
        separator = "/"
        # set up expected output
        expected = "level1/level2", "level3"
        # run test
        actual = p.getPreviousLevel(var, separator)
        # asserts
        self.assertEqual(expected, actual, "level not as expected")

    def test_getNextLevel_notFound(self):
        # initialize
        jsonOutput = {
            "failures": [],
            "errors": []
        }
        p = terraform_validate.PreProcessor(jsonOutput)
        var = "dir"
        separator = "/"
        # set up expected output
        expected = "dir", ""
        # run test
        actual = p.getNextLevel(var, separator)
        # asserts
        self.assertEqual(expected, actual, "level not as expected")

    def test_getNextLevel_found(self):
        # initialize
        jsonOutput = {
            "failures": [],
            "errors": []
        }
        p = terraform_validate.PreProcessor(jsonOutput)
        var = "level1/level2/level3"
        separator = "/"
        # set up expected output
        expected = "level1", "level2/level3"
        # run test
        actual = p.getNextLevel(var, separator)
        # asserts
        self.assertEqual(expected, actual, "level not as expected")

    def test_add_failure(self):
        # initialize
        jsonOutput = {
            "failures": [],
            "errors": []
        }
        p = terraform_validate.PreProcessor(jsonOutput)
        failure1 = "some failure"
        moduleName1 = "a module name"
        fileName1 = "the file name"
        severity1 = "high"
        failure2 = "another failure"
        moduleName2 = "some other module name"
        fileName2 = "another file name"
        severity2 = "low"
        # set up expected outputs
        expected = []
        expectedFailure1 = {}
        expectedFailure1["severity"] = severity1
        expectedFailure1["message"] = failure1
        expectedFailure1["moduleName"] = moduleName1
        expectedFailure1["fileName"] = fileName1
        expectedFailure2 = {}
        expectedFailure2["severity"] = severity2
        expectedFailure2["message"] = failure2
        expectedFailure2["moduleName"] = moduleName2
        expectedFailure2["fileName"] = fileName2
        expected.append(expectedFailure1)
        expected.append(expectedFailure2)
        # run test
        p.add_failure(failure1, moduleName1, fileName1, severity1)
        p.add_failure(failure2, moduleName2, fileName2, severity2)
        # asserts
        self.assertEqual(2, len(p.jsonOutput["failures"]), "should have been 12 failures")
        self.assertEqual(expected, p.jsonOutput["failures"], "failure message isn't as expected")

    def test_add_error_notAdded_pass1(self):
        # initialize
        jsonOutput = {
            "failures": [],
            "errors": []
        }
        p = terraform_validate.PreProcessor(jsonOutput)
        p.passNumber = 1
        p.shouldLogErrors = True
        error = "some error"
        moduleName = "a module name"
        fileName = "the file name"
        severity = "high"
        # run test
        p.add_error(error, moduleName, fileName, severity)
        # asserts
        self.assertEqual(0, len(p.jsonOutput["errors"]), "should have been 0 errors")

    def test_add_error_notAdded_shouldLogErrorsFalse(self):
        # initialize
        jsonOutput = {
            "failures": [],
            "errors": []
        }
        p = terraform_validate.PreProcessor(jsonOutput)
        p.passNumber = 2
        p.shouldLogErrors = False
        error = "some error"
        moduleName = "a module name"
        fileName = "the file name"
        severity = "high"
        # run test
        p.add_error(error, moduleName, fileName, severity)
        # asserts
        self.assertEqual(0, len(p.jsonOutput["errors"]), "should have been 0 errors")

    def test_add_error_added(self):
        # initialize
        jsonOutput = {
            "failures": [],
            "errors": []
        }
        p = terraform_validate.PreProcessor(jsonOutput)
        p.passNumber = 2
        p.shouldLogErrors = True
        error = "some error"
        moduleName = "a module name"
        fileName = "the file name"
        severity = "high"
        # set up expected outputs
        expected = {}
        expected["severity"] = severity
        expected["message"] = error
        expected["moduleName"] = moduleName
        expected["fileName"] = fileName
        # run test
        p.add_error(error, moduleName, fileName, severity)
        # asserts
        self.assertEqual(1, len(p.jsonOutput["errors"]), "should have been 1 error")
        self.assertEqual(expected, p.jsonOutput["errors"][0], "error message isn't as expected")

    def test_getFailureMsg(self):
        # initialize
        jsonOutput = {
            "failures": [],
            "errors": []
        }
        p = terraform_validate.PreProcessor(jsonOutput)
        severity = "high"
        msg = "some message"
        moduleName = "a module name"
        fileName = "the file name"
        # set up expected outputs
        expected = {}
        expected["severity"] = severity
        expected["message"] = msg
        expected["moduleName"] = moduleName
        expected["fileName"] = fileName
        # run test
        actual = p.getFailureMsg(severity, msg, moduleName, fileName)
        # asserts
        self.assertEqual(expected, actual, "failure message isn't as expected")


if __name__ == '__main__':
    unittest.main()
