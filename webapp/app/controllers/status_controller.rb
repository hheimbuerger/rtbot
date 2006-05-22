#require 'apis/bot_api'
class BotApi < ActionWebService::API::Base
  api_method 'PluginList', :returns => [[:string]]
end

class StatusController < ApplicationController
#  before_filter :login_required
  layout 'main'
#  web_client_api 'BotApi', :xmlrpc, "http://localhost:8000/"

  def index
#    @plugin_list = pluginList()
    begin
      bot = ActionWebService::Client::XmlRpc.new(BotApi, "http://localhost:8000/")
      @plugins = bot.PluginList
      @has_connection = true
    rescue Errno::ECONNREFUSED
      @has_connection = false
    end
  end
end
