class Permission < ActiveRecord::Base
  has_and_belongs_to_many :users
  
  def isUserAllowed(user_id)
#    breakpoint "a"
    #logger.info("=== start ===")
    users.each do |user|
      #logger.info(user.id)
      #logger.info(user_id)
      #logger.info((user.id.to_s() == user_id.to_s()).to_s())
      if user.id.to_s() == user_id.to_s() then
        #logger.info("TRUE")
        return(true)
      end
    end
    #logger.info("FALSE")
    return(false)
  end
end
