s.boot;

SynthDef(\drone, { |out, freq = 440, gate = 0.5, amp = 1.0, attack = 0.04, release=0.1 |
	var sig,nsize,n = (2..20);
	nsize = n.size;
	sig = ((
		n.collect {arg i; 
			SinOsc.ar( (1.0 - (1.0/(i*i))) * freq )
		}).sum / nsize)
	* EnvGen.kr(Env.adsr(attack, 0.2, 0.6, release), gate, doneAction:2)
	* amp;
    Out.ar(out, sig ! 2)
}).add;

~drone = Synth(\drone,[\amp,0.1]);

~makeLinSetter = {|mySynth,param,low2=0.0,hi2=1.0,low=0.0,hi=1.0| 
	{|msg|
		var val = msg[1].linlin(low,hi,low2,hi2);
		// [msg[0],msg[1],val].postln;
		mySynth.set(param, val)
	}
};
~makeExpSetter = {|mySynth,param,low2=0.0,hi2=1.0,low=0.0,hi=1.0| 
	{|msg|
		msg.postln;
		mySynth.set(param,msg[1].linexp(low,hi,low2,hi2))
	}
};

OSCFunc.newMatching(~makeExpSetter.(~drone,\freq,100,10000,0,15), '/entropy');
