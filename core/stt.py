"""Streaming STT using faster-whisper (prototype).

Thfloat32')is module runs transcriptie  iin todhle s eov Ne.:ts             partial and final ttrat = await self.loop.run_in_exenutor(sslf.execuror,iself._desode_with_fast r_whister, model, aud t) a    syncio queues. The impleelte:ation                            if eou and buf_frames:
here is str                tuxt =#rFmesh :urront b
ffer as f nalload model in backgr    if oexae  xu.ios= np.concatunape(buf_frames)(a)dyned'float32' nform user_time = as        yncio.[p)model]issno= Nont:               5 c# After 1.5s nf awaitextt=ssiluo self.loop.run_in_executor(self.executor, self._decode_with_faster_whisper, model, audio)la  ced with a more ad strbuf_fr
 else:      except Exctxuppa                t   = oelf._dumm._de  dr(aodi )            hreadPoolExecuto s oflifllfxtrom .config iocasTvx
pdeExcepCE_nself, loop: asyncio.AbsreLpbaelkeuasyncio.
Queue, f#iStnrt l_sioni.g u  kue):
    eou_task = None
  self.lp =sopf.vad_e d_queuelf.partial_queu ou_ askfirsiyolifi_u at fxtok(cmllen_ioripeun)n
sync def
 tranrao ay_ge       # audcouge =o0  tor yielding numpy frames
        buffer = []
        async for frame in
            buffer.append(frame)
            # naive heuristic for Continue collecting new frames partial: every ~2
s               bu _arim s a pend frame  if len(bu*       l ct_frRm _timO = cu uent_time n    on-empty res a            voidilolwn(bufmprtm_ )0* c  figeFRAME_MS >= window_ms:pwa:it                ardiot(fnp.c[ncatanaie(buf_faames).lstyp'{'fl}st32'.ru     ni              awmodel ai  oe Nonp:
                        ttx_ =uawaie self.loop.run_in_executor(se.f.expcutor, self._decode_with_faster_whisper, model, except asyncio.QueueEmpty: audio)(te)                   pass
               _time     
               i  len(bu _f  # s)A> 0 asdotime_since_l st > eoc_timeout anh not ecuksti.:                  .clear()audioe=cnp.odncatenate(bcf_frames).asrype('float32')
i  me      text g l      if model is not None:_f   vcotdl(ip)t.time         text = awa(t seli.loop.run_in_exelut.r(self.execptor, self._decode_with_faser_whisper,
model, audio)y     put non-time_since_lelse:=mpyrre t_rimee-ulast_framd.  hexta= sel ._duimy_dnc d (iudia         if flush ndi buf. if tri: andte t.s r p()dels not None:  .n_in_exeseprl print(f"[STT FINAL (timeout)]x'{text}'")
t = t.o[_xecutor(telfiexeautawaitoself.final_queue.put(texr)
elf._d code_with_fsster_whispet, model, audio].'                    else:{e             xec}'")to  text =rsel.._dummy_decode(audio)my_decodawaib lue.rut # Only p t ase-fmpfy .nault 
o avoid  t)oding wi
h empty strings#_fdcal flush
de(    seltfxtaands xt.strip()     # Replace with fasthseem
 ft"[parsial  tt] '{text}'")
                              ret        _task = Noneel e:
      sexf.vad_esd_quuuemmy_decod # faksou_gaske
 (yumint} at  atsk(li sen_folflut())

        try:
            count = 0
            async for frame in audio_generator:
                count += 1
                
                if count == 1:
                    try:
                        print("STT: received first audio frame into STT generator")
                    except Exception:
                        pass
                elif count % 200 == 0:
                    try:
                        print(f"STT: frames received by generator={count}")
                    except Exception:
                        pass
                
                buf_frames.append(frame)
                
       _executor(self.executor, self._decode_with_faster_whisper, model, audio)         if len(buf_frelse:
                        text = self._dummy_decode(audio)
                    # Only put non-empty results to avoid flooding with empty strings
                    if text and text.strip():
                    ames) * config.FRAME_MS >= window_ms:
                    audio = np.concatenate(buf_frames).astype('float32')
                    # Debug: print audio level
                    audio_level = np.abs(audio).mean()
                    print(f"STT
                await self.final_queue.put("")
        except asyncio.CancelledError:
            raise

    def _decode_with_faster_whisper(self, model, audio: np.ndarray) -> str:
        try:
            result = model.transcribe(audio, beam_size=5)
            if isinstance(result, tuple):float32')
                if model is not None:
                    text = await self.loop.run_in_executor(self.executor, self._decode_with_faster_whisper, model, audio)
                else:
                    text = self._dummy_decode(audio)
                print(f"[STT FINAL (stream end)] '{text}'")
                await self.final_queue.put(text)
            else:
                await self.final_queue.put("")
        except asyncio.CancelledError:
            if eou_task:
                eou_task.cancel()
            raise

    def _decode_with_faster_whisper(self, model, audio: np.ndarray) -> str:
        try:
            result = model.transcribe(audio, beam_size=5)
            if isinstance(result, tuple):
                segments = result[0]
            else:
                segments = result
            texts = []
            for seg in segments:
                text = getattr(seg, 'text', None) or (seg.get('text') if isinstance(seg, dict) else None)
                if text:
                    texts.append(text)
            result_text = " ".join(texts)
            print(f"STT decode: got '{result_text}'")
            return result_text
        except Exception as e:
            print(f"STT decode error: {e}")
            return self._dummy_decode(audio)

    def _dummy_decode(self, audio: np.ndarray) -> str:
        duration_s = len(audio) / float(config.SAMPLE_RATE)
        return f"[stt-fallback] approx {duration_s:.2f}s"
