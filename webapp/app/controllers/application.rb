# Filters added to this controller will be run for all controllers in the application.
# Likewise, all the methods added will be available for all controllers.
require_dependency "login_system"

class ApplicationController < ActionController::Base
  include LoginSystem
  model :user
  
  def self.allow_with_permission(params)
  #def self.allow_with_permission(*roles)
    #conditions = extract_conditions!(roles)
    #print "called! #{conditions.inspect} | #{roles.inspect} \n"
    #before_filter(conditions) do |controller|
    before_filter(:only => params[:action]) do |controller|
      #print "controller.session: #{controller.session.inspect} \n"
      #print "in Filter!: #{roles.inspect}\n"
      #roles.each {|role| return if has_permission?(role, controller.session)}
      if not controller.session[:user] or (params[:required_permission] and not has_permission?(params[:required_permission], controller.session))
        controller.access_denied!(controller, params[:required_permission])
      end
    end
  end

  def self.has_permission?(permission_handle, session_hash)
    #print "@session: #{session_hash.inspect}\n"
    #print "authorize?(session_hash[:user]): #{authorize?(session_hash[:user].inspect)}\n"
    if session_hash[:user]      # and authorize?(session_hash[:user])
      permission = Permission.find(:first, :conditions => ["handle = ?", permission_handle])
      #print "Permission: #{permission.inspect}\n"
      return(permission.isUserAllowed(session_hash[:user].id))
    end
      return false
  end
  
  def access_denied!(controller, required_permission)
    #print "controller: #{controller.inspect}\n"
    flash[:errormessage] = "You're missing the required permissions."
    flash[:required_permission] = required_permission
    flash[:referrer] = "#{controller.request.parameters[:controller]}##{controller.request.parameters[:action]}"
    redirect_to :controller => 'permission', :action => 'access_denied'
    return(false)
  end  
  
end