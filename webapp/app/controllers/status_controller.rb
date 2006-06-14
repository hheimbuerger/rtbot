class StatusController < ApplicationController
#  before_filter :login_required
  layout 'main'
  include BotConnectionHelper
#  web_client_api 'BotApi', :xmlrpc, "http://localhost:8000/"

  # /=============================================
  # | PERMISSIONS
  # \=============================================
  # index: public
  # internal: logged in
  allow_with_permission :action => 'internal', :required_permission => nil

private
  def prepare_status_data
    get_status
  end

public
  def index
    if(@session[:user])
      redirect_to :action => 'internal'
    end
    prepare_status_data
  end
  
  def internal
    prepare_status_data  
  end
end
