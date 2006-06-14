class StatusController < ApplicationController
#  before_filter :login_required
  layout 'main'
  include BotConnectionHelper
#  web_client_api 'BotApi', :xmlrpc, "http://localhost:8000/"

  def index
    
  end
end
