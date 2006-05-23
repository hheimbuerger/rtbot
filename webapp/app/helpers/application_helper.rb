# Methods added to this helper will be available to all templates in the application.
module ApplicationHelper
  include LoginSystem

  # check permissions
  def has_permission?(permission_handle)
    if @session[:user] and authorize?(@session[:user])
      permission = Permission.find(:first, :conditions => ["handle = ?", permission_handle])
      return(permission.isUserAllowed(@session[:user].id))
    end
      return false
  end

end
