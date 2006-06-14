class BotApi < ActionWebService::API::Base
  inflect_names false
  
  # PluginStatusList() == list(list(name, enabled, online)) == [[A, true, true], [B, false, false]]
  api_method 'pluginStatusList', :returns => [[[:string], [:bool], [:bool]]]
  
  api_method 'enablePlugin', :expects => [:string]
  api_method 'disablePlugin', :expects => [:string]
  
  #class BotApi < ActionWebService::API::Base
  api_method 'retrieveLogWatchTicket', :returns => [:int]
#end
  
end
