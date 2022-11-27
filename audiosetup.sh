#!/bin/bash
pushd ~/projects/mixer
gnome-terminal --profile=Pink -- bash drop-connect-monitor.sh &
popd
sleep 6
jack_connect system:capture_2    csoundDropMixer:input2
jack_connect SuperCollider:out_1 csoundDropMixer:input1
jack_connect SuperCollider:out_2 csoundDropMixer:input1
jack_disconnect SuperCollider:out_1 system:playback_1
jack_disconnect SuperCollider:out_2 system:playback_2
bash orangecopyandpaste.sh

