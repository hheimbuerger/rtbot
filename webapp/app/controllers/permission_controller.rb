class PermissionController < ApplicationController
  before_filter :login_required
  layout 'main'

  def index
    @permissions = Permission.find_all
    user = @session[:user]
#    breakpoint "Breaking"
  end

end
