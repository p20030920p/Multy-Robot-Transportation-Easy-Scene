
(cl:in-package :asdf)

(defsystem "smart_factory_sim-srv"
  :depends-on (:roslisp-msg-protocol :roslisp-utils )
  :components ((:file "_package")
    (:file "AssignTask" :depends-on ("_package_AssignTask"))
    (:file "_package_AssignTask" :depends-on ("_package"))
    (:file "ProcessMaterial" :depends-on ("_package_ProcessMaterial"))
    (:file "_package_ProcessMaterial" :depends-on ("_package"))
  ))