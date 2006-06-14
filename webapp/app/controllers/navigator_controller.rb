class NavigatorController < ApplicationController
  include ApplicationHelper

  # /=============================================
  # | PERMISSIONS
  # \=============================================
  # free for all

  def index
    @is_superadmin = has_permission?("superadmin")
  end
end
