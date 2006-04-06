class ExceptionsController < ApplicationController
  before_filter :login_required
  layout 'main'

  def index
    if(has_permission?("viewexc"))
      @state = "yes"
    else
      @state = "no"
    end
  end
end
