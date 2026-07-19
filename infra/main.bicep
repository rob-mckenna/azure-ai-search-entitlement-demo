targetScope = 'subscription'

@minLength(1)
@maxLength(64)
@description('Name of the environment which is used to generate a short unique hash for all resources.')
param environmentName string

@minLength(1)
@description('Primary location for all resources')
param location string

@description('Id of the user or app to assign application roles')
param principalId string = ''

var abbrs = loadJsonContent('./abbreviations.json')
var resourceToken = toLower(uniqueString(subscription().id, environmentName, location))
var tags = { 'azd-env-name': environmentName }

// Resource group
resource rg 'Microsoft.Resources/resourceGroups@2021-04-01' = {
  name: '${abbrs.resourcesResourceGroups}${environmentName}'
  location: location
  tags: tags
}

// User-assigned managed identity for the application
module identity 'br/public:avm/res/managed-identity/user-assigned-identity:0.2.1' = {
  name: 'identity'
  scope: rg
  params: {
    name: '${abbrs.managedIdentityUserAssignedIdentities}${resourceToken}'
    location: location
    tags: tags
  }
}

// Azure AI Search
module searchService 'br/public:avm/res/search/search-service:0.12.2' = {
  name: 'search'
  scope: rg
  params: {
    name: '${abbrs.searchSearchServices}${resourceToken}'
    location: location
    tags: tags
    sku: 'standard'
    replicaCount: 1
    partitionCount: 1
    hostingMode: 'Default'
    publicNetworkAccess: 'Enabled'
    authOptions: {
      aadOrApiKey: {
        aadAuthFailureMode: 'http403'
      }
    }
    roleAssignments: principalId != '' ? [
      {
        principalId: principalId
        roleDefinitionIdOrName: 'Search Index Data Contributor'
        principalType: 'User'
      }
      {
        principalId: identity.outputs.principalId
        roleDefinitionIdOrName: 'Search Index Data Contributor'
        principalType: 'ServicePrincipal'
      }
    ] : [
      {
        principalId: identity.outputs.principalId
        roleDefinitionIdOrName: 'Search Index Data Contributor'
        principalType: 'ServicePrincipal'
      }
    ]
  }
}

// Storage account for sample documents
module storageAccount 'br/public:avm/res/storage/storage-account:0.9.1' = {
  name: 'storage'
  scope: rg
  params: {
    name: '${abbrs.storageStorageAccounts}${resourceToken}'
    location: location
    tags: tags
    kind: 'StorageV2'
    skuName: 'Standard_LRS'
    allowBlobPublicAccess: false
    publicNetworkAccess: 'Enabled'
    blobServices: {
      containers: [
        {
          name: 'sample-documents'
          publicAccess: 'None'
        }
      ]
    }
    roleAssignments: principalId != '' ? [
      {
        principalId: principalId
        roleDefinitionIdOrName: 'Storage Blob Data Contributor'
        principalType: 'User'
      }
      {
        principalId: identity.outputs.principalId
        roleDefinitionIdOrName: 'Storage Blob Data Contributor'
        principalType: 'ServicePrincipal'
      }
    ] : [
      {
        principalId: identity.outputs.principalId
        roleDefinitionIdOrName: 'Storage Blob Data Contributor'
        principalType: 'ServicePrincipal'
      }
    ]
  }
}

// App Service Plan
module appServicePlan 'br/public:avm/res/web/serverfarm:0.7.0' = {
  name: 'appServicePlan'
  scope: rg
  params: {
    name: '${abbrs.webServerFarms}${resourceToken}'
    location: location
    tags: tags
    skuName: 'B1'
    skuCapacity: 1
    reserved: true
  }
}

// App Service (Backend API)
module appService 'br/public:avm/res/web/site:0.23.1' = {
  name: 'appService'
  scope: rg
  params: {
    name: '${abbrs.webSitesAppService}${resourceToken}'
    location: location
    tags: union(tags, { 'azd-service-name': 'api' })
    kind: 'app,linux'
    serverFarmResourceId: appServicePlan.outputs.resourceId
    siteConfig: {
      linuxFxVersion: 'PYTHON|3.11'
      appCommandLine: 'uvicorn main:app --host 0.0.0.0 --port 8000'
      alwaysOn: true
      appSettings: [
        {
          name: 'AZURE_SEARCH_ENDPOINT'
          value: 'https://${searchService.outputs.name}.search.windows.net'
        }
        {
          name: 'AZURE_SEARCH_INDEX'
          value: 'entitlement-demo-index'
        }
        {
          name: 'AZURE_CLIENT_ID'
          value: identity.outputs.clientId
        }
        {
          name: 'ENABLE_LLM'
          value: 'false'
        }
        {
          name: 'SCM_DO_BUILD_DURING_DEPLOYMENT'
          value: 'true'
        }
      ]
    }
    managedIdentities: {
      userAssignedResourceIds: [identity.outputs.resourceId]
    }
  }
}

// Log Analytics Workspace
module logAnalytics 'br/public:avm/res/operational-insights/workspace:0.4.0' = {
  name: 'logAnalytics'
  scope: rg
  params: {
    name: '${abbrs.operationalInsightsWorkspaces}${resourceToken}'
    location: location
    tags: tags
    skuName: 'PerGB2018'
    dataRetention: 30
  }
}

// Application Insights
module appInsights 'br/public:avm/res/insights/component:0.4.0' = {
  name: 'appInsights'
  scope: rg
  params: {
    name: '${abbrs.insightsComponents}${resourceToken}'
    location: location
    tags: tags
    workspaceResourceId: logAnalytics.outputs.resourceId
    applicationType: 'web'
    kind: 'web'
  }
}

// Outputs used by azd and application configuration
output AZURE_LOCATION string = location
output AZURE_TENANT_ID string = tenant().tenantId
output AZURE_RESOURCE_GROUP string = rg.name
output AZURE_SEARCH_ENDPOINT string = 'https://${searchService.outputs.name}.search.windows.net'
output AZURE_SEARCH_INDEX string = 'entitlement-demo-index'
output AZURE_STORAGE_ACCOUNT string = storageAccount.outputs.name
output AZURE_APP_SERVICE_URL string = 'https://${appService.outputs.defaultHostname}'
output APPLICATIONINSIGHTS_CONNECTION_STRING string = appInsights.outputs.connectionString
