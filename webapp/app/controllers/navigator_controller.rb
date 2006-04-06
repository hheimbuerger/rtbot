class NavigatorController < ApplicationController

  def index
    @is_superadmin = has_permission?("superadmin")
  end
end