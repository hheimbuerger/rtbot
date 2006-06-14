class ManagerController < ApplicationController
  #before_filter :login_required
  layout 'main'
  include BotConnectionHelper

  # /=============================================
  # | PERMISSIONS
  # \=============================================
  # index: requires login
  # kill: requires 'killproc'
  # call: requires 'mancore'
  # enable: requires 'manplugins'
  # disable: requires 'manplugins'
  allow_with_permission :action => 'index', :required_permission => nil
  allow_with_permission :action => 'kill', :required_permission => 'killproc'
  allow_with_permission :action => 'call', :required_permission => 'mancore'
  allow_with_permission :action => 'enable', :required_permission => 'manplugins'
  allow_with_permission :action => 'disable', :required_permission => 'manplugins'

private
  def get_process_list
    didFindOne = false
    output = `ps x -o "%p|%a"`
    #output = "23233|python BotManager.py restart\n" \
    #         "30891|su rtbot\n" \
    #         "30892|bash\n" \
    #         "31191|ps x -o %p|%a"
    re = /^(\d+)\|(.*)$/
    if(output) then
      result = []
      output.split("\n").each do |line|
        md = re.match(line)
        if(not md.nil?) then
          didFindOne = true
          if(md[2].include? "python BotManager") then
            result << {:pid => md[1], :command => md[2]}
          end
        end
      end
      return(result)
    else
      return(nil)
    end
  end


public

  def index
    @processes = get_process_list
    #print "now accessing XML_RPC\n"
    @plugin_list = get_plugin_status_list
  end
  
  def kill
    get_process_list.each do |process|
      #print "\n|#{process[:pid]}|#{params[:pid]}|\n"
      if(process[:pid] == params[:pid]) then
        flash[:results] = `kill #{process[:pid]}`
        break
      end
    end
    redirect_to :action => 'index'
  end
  
  def call
    print params[:type]
    if(params[:type] == 'start') then
      flash[:results] = `cd #{BOT_PATH} && python BotManager.py start 2>&1`
    elsif(params[:type] == 'restart') then
      flash[:results] = `cd #{BOT_PATH} && python BotManager.py restart 2>&1`
    elsif(params[:type] == 'stop') then
      flash[:results] = `cd #{BOT_PATH} && python BotManager.py stop 2>&1`
    end
    redirect_to :action => 'index'
  end
  
  def enable
    enable_plugin(params[:plugin])
    redirect_to :action => 'index'
  end
  
  def disable
    disable_plugin(params[:plugin])
    redirect_to :action => 'index'
  end

end
