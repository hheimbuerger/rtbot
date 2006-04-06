require File.dirname(__FILE__) + '/../test_helper'
require 'navigator_controller'

# Re-raise errors caught by the controller.
class NavigatorController; def rescue_action(e) raise e end; end

class NavigatorControllerTest < Test::Unit::TestCase
  def setup
    @controller = NavigatorController.new
    @request    = ActionController::TestRequest.new
    @response   = ActionController::TestResponse.new
  end

  # Replace this with your real tests.
  def test_truth
    assert true
  end
end
