class ManagerController < ApplicationController
  before_filter :login_required
  layout 'main'

  def index
  end
end
