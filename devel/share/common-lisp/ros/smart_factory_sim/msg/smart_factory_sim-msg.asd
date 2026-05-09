
(cl:in-package :asdf)

(defsystem "smart_factory_sim-msg"
  :depends-on (:roslisp-msg-protocol :roslisp-utils :geometry_msgs-msg
)
  :components ((:file "_package")
    (:file "MachineState" :depends-on ("_package_MachineState"))
    (:file "_package_MachineState" :depends-on ("_package"))
    (:file "MaterialInfo" :depends-on ("_package_MaterialInfo"))
    (:file "_package_MaterialInfo" :depends-on ("_package"))
    (:file "TaskStatus" :depends-on ("_package_TaskStatus"))
    (:file "_package_TaskStatus" :depends-on ("_package"))
  ))