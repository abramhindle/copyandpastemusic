s.quit;
s.options.numBuffers = 16000;
s.options.memSize = 1000000;
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

SynthDef.new(\pb,{
	arg output= 0, bufnum = 0, start=0, loop = 0, rate = 1.0, duration=1.0, amp=1.0;
	var env = Env.sine(dur: duration, level: amp);
	Out.ar(output,
		EnvGen.kr(env, doneAction: Done.freeSelf) * 
		PlayBuf.ar(1, bufnum, rate, BufRateScale.kr(bufnum), startPos: SampleRate.ir*start, loop: loop, doneAction: 2));
}).load(s);


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


~loadingBuffers = Dictionary();
~buffers = Dictionary();
~duration = 2.0;
~amp = 0.1;
~triggerGrain = {
	arg filename, offset=0;
	var buf;
	if( ~loadingBuffers.at(filename) == nil,
		{
			~loadingBuffers.put(filename,True);
			("Loading "+filename).postln;
			buf = Buffer.read(s,filename,action: {
				|buf|
				~buffers.put(filename,Buffer.read(s,filename));
				("Loaded "+filename).postln;
			}
            );
		},
		{
		}
	);
	buf = ~buffers.at(filename);
	Synth(\pb,[\output,0,\bufnum,buf,\start, (offset / 5.166666666), \duration, ~duration, \amp, ~amp]);
};

		/*
			~triggerGrain.('/opt/hindle1/Music/48kmonos/Kimiko_Ishizaka_-_Bach-_Well-Tempered_Clavier,_Book_1_-_15_Prelude_No._8_in_E-flat_minor,_BWV_853.flac.wav',4.linrand + 30);

		*/

		
OSCFunc.newMatching({
	|msg|
	var filename, offset;
	filename = msg[1];
	offset = msg[2];
	// ("Play " + filename + " " + offset).postln;
	~triggerGrain.( filename, offset );
}, '/grain');


~testplaythis = ['/mappingchain','/opt/hindle1/Music/48kmonos/ZOOM0001-some-noise-maybe-hiroshima.WAV.split011.wav', 99, '/opt/hindle1/Music/48kmonos/skruntskrunt-drone-day-instrumental.flac.wav.split032.wav', 98, '/opt/hindle1/Music/48kmonos/ZOOM0006-noise.WAV.split010.wav', 68, '/opt/hindle1/Music/48kmonos/15-Bruno_Bettinelli-Libere_e_lievi.wav', 303, '/opt/hindle1/Music/48kmonos/skruntskrunt-i-want-to-touch-my-face.flac.wav', 242, '/opt/hindle1/Music/48kmonos/skruntskrunt-i-want-to-touch-my-face.flac.wav', 242, '/opt/hindle1/Music/48kmonos/skruntskrunt-and-digital---information-retrieval.flac.wav.split015.wav', 89, '/opt/hindle1/Music/48kmonos/skruntskrunt-sweep-for-HNW-4k.wav', 1557];

~chainbeat = 0.5;

~mappingchain = {
	|msg|
	Routine({
		forBy( 1, msg.size - 1, 2, {
			arg i;
			var filename = msg[i], offset = msg[i+1];
			("Play " + filename + " " + offset).postln;
			~triggerGrain.( filename, offset );
			~chainbeat.wait;
		});
	}).play;

};

~mappingchain.(~testplaythis);

OSCFunc.newMatching(~mappingchain, '/mappingchain');

/*





*/