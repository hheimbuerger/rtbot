module FileHelper
    def self.append_features(controller) #:nodoc:
        if controller.ancestors.include? ActionController::Base
            controller.add_template_helper self
        else
            super
        end
    end

    def link_download(file, caption)
        link_to CGI.escapeHTML(caption), :controller => 'file', :action => 'download',
                :params => { 'file' => file }
    end
end
