class LogsController < ApplicationController
  #before_filter :login_required
  layout 'main'
  include FileHelper
  include BotConnectionHelper

  # /=============================================
  # | PERMISSIONS
  # \=============================================
  # index: requires 'viewlogs'
  # register: requires 'watchlogs'
  # update: requires 'watchlogs'
  allow_with_permission :action => 'index', :required_permission => 'watchlogs'
  allow_with_permission :action => 'register', :required_permission => 'watchlogs'
  allow_with_permission :action => 'update', :required_permission => 'watchlogs'

  def index
    @my_dir = Dir.new(BOT_PATH + "logs/")
  end
  
  def register
    session[:ticket] = get_logging_ticket
  end
  
  def update
    #render :text => "Hello, world!<br/>1<br/>2<br/>3<br/>4<br/>5<br/>6<br/>7<br/>8<br/>9<br/>0"
    if(session[:ticket])
      begin
        bot = ActionWebService::Client::XmlRpc.new(BotApi, "http://localhost:8000/")
        messages = bot.GetLogMessages(session[:ticket])
        if(messages.length == 0)
          render :text => "No new messages.<br/>"
        else
          render :text => messages.join("<br/>") + "<br/>"
        end
      rescue Errno::ECONNREFUSED, Errno::EBADF
        render :text => "Update: Can't connect to the bot via XML-RPC.<br/>"
      end
    else
      render :text => "Update: No ticket found in the session hash."
    end
  end
end
