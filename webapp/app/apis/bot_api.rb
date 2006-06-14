class BotApi < ActionWebService::API::Base
  inflect_names false
  
  api_method 'getStatus', :returns => [[[:string], [:int], [:int]]]
  # PluginStatusList() == list(list(name, enabled, online)) == [[A, true, true], [B, false, false]]
  api_method 'pluginStatusList', :returns => [[[:string], [:bool], [:bool]]]
  
  api_method 'enablePlugin', :expects => [:string]
  api_method 'disablePlugin', :expects => [:string]
  
  api_method 'retrieveLogWatchTicket', :expects => [:string, [:string], [:string]], :returns => [:int]
  api_method 'getLogMessages', :expects => [:string], :returns => [[:string]]
  api_method 'stopWatching', :expects => [:string]
  
end
