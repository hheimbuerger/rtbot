require 'action_web_service'
require 'singleton'



class XMLRPCClient < ActionWebService::API::Base
  include Singleton
  inflect_names false
  api_method :status, :expects => [], :returns => [:string]

  def initialize()
    sp = ActionWebService::Client::XmlRpc.new(XMLRPCClient, "http://localhost:8000/")
  end
end

a = sp.pluginList()
