# Filters added to this controller will be run for all controllers in the application.
# Likewise, all the methods added will be available for all controllers.
require_dependency "login_system"

class ApplicationController < ActionController::Base
  include LoginSystem
  model :user
  
  # =======================================================
  # | DEBUG: THIS SHOULD BE REMOVED, BUT THE CONTROLLERS SUDDENLY STOPPED 
  # | FINDING THE METHOD IN APPLICATION_HELPER.RB
  # =======================================================
  # check permissions
  def has_permission?(permission_handle)
    if @session[:user] and authorize?(@session[:user])
      permission = Permission.find(:first, :conditions => ["handle = ?", permission_handle])
      return(permission.isUserAllowed(@session[:user].id))
    end
      return false
  end
  # =======================================================
  # | END
  # =======================================================
end