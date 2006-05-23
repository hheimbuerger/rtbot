#require 'application'
#require 'file_helper'

    class MissingFile < ActionController::ActionControllerError #:nodoc:
    end

class FileController < ApplicationController
  before_filter :login_required, :except => ['filenotfound', 'download']
  layout 'main'
    include FileHelper

    #class MissingFile < ActionController::ActionControllerError #:nodoc:
    #end
    
  private
    def index
    end

  protected
    def base_path
        #File.dirname(__FILE__)
        BOT_PATH
    end

    def permit_file?(path)
        has_permission?("viewlogs")
        #true
        #@session['user'] and @session['user'].permit_file?(path)
    end

  public
#    def index
#        #to_root = '../' * File.dirname(__FILE__).count(File::SEPARATOR)
#        to_root = BOT_PATH + "logs/"
#
#        @good = [ File.basename(__FILE__) ]

#        @bad  = [
#            '../<< "&',
#            '/tmp/mysql.sock',
#            '/etc/passwd',
#            "#{to_root}etc/passwd",
#            '`cat /etc/passwd`',
#            '../../config/database.yml',
#        ]
#    end
    def filenotfound
    end

    def download
        begin
            path = sanitize_file_path(@params['file'], base_path)
            raise MissingFile, 'permission denied' unless permit_file? path

            if http_if_modified_since? path
                send_file path
            else
                render_text '', '304 Not Modified'
            end

        rescue MissingFile => e
            flash['error'] = "Download error: #{e} / #{path}" 
            redirect_to :action => 'filenotfound'
        end
    end

  protected
    # Safely resolve an absolute file path given a malicious filename.
    def sanitize_file_path(filename, base_path)
        # Resolve absolute path.
        path = File.expand_path("#{base_path}/#{filename}")
        logger.info("Resolving file download:  #{filename}\n => #{base_path}/#{filename}\n => #{path}") unless logger.nil?

        # Deny ./../etc/passwd and friends.
        # File must exist, be readable, and not be a directory, pipe, etc.
        raise MissingFile, "couldn't read #{filename}" unless
            path =~ /^#{File.expand_path(base_path)}/ and
            File.readable?(path) and
            File.file?(path)

        return path
    end

    # Check whether the file has been modified since the date provided
    # in the If-Modified-Since request header.
    def http_if_modified_since?(path)
        if since = @request.env['HTTP_IF_MODIFIED_SINCE']
            begin
                require 'time'
                since = Time.httpdate(since) rescue Time.parse(since)
                return since < File.mtime(path)
            rescue Exception
            end
        end
        return true
    end
end