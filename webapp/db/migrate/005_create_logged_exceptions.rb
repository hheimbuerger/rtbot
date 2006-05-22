class CreateLoggedExceptions < ActiveRecord::Migration
  def self.up
    create_table :logged_exceptions do |t|
      # t.column :name, :string
    end
  end

  def self.down
    drop_table :logged_exceptions
  end
end
