"""Main runner wiring the modules into an async pipeline.

Prototype behavior:
- capture audio frames -> VAD -> build utterances -> send to STT
- stream partial STT to console
- on final STT, send prompt to LLM and stream tokens
- chunk LLM into sentences -> TTS -> playback
- support interrupt: when VAD detects speech during speaking, cancel playback and LLM

This is a prototype to demonstrate architecture; replace placeholders
with production-grade model integrations when ready.
"""
import asyncio
from core.co            except Exception:nfig impor        passt config
roa silunci_couo_ = 0nput imporelt Avuount %500o==o0_output import AudioOutput
from core.vad ifmport hDartbSat"(frame) pcocess
r={vcount}")om corexcepteExcettion:port STTSe        passrvice
fro l  lm i
mpo_    # Track c em. = fpr erd-of-utteranceSeeeif
vfm cspeaki0grom detttrynal if is_speech STT to flusprhnt( sAleD=o_)upt_ = 0
n    pads auel e:vad
_end_e# Track fwr(en_c oqt += 1pre endpfa        ki gnlecce_count >= SILENCE_THRESHOLDo.Qu)x,aiesis_s        pttvad:und_qucue:
                        try: r            eceived fsildicevad_mnd_queus.put=n0wait(Trme)
              ldco n else:waprint("Vd_event_quesilence_countu+=e1
.put(is_sp e    i
sil   f_=oun  >= SILENCE_THRESHOLD:nt} frames")e.get()
 if vad_ nd_quiueone    :
            breaktry:

      nd SAME frame to BOTvad_ADd_queua.putnn wait(TrSe)
           await fre_generapr_r  "ame_generator_stt.put(frame)_speech(frame)


asynr(frame_gevcountn+=e1asyncio.Queue, vad_eveohowuVAD uv,etsrrupt_mgr:if is_sp nchrandptot sMntkieg:upt_mgr: IaatttCn:tate, vad_d_queue:pri  ("VAD:#speechIstarted")
PLER APPROACH: Just detect if
    speaking = Fal is_speech and not speaking:s        speaking = is_speeche
    while suate.se
 lisIenEnNTHRESHOLD =  f fot is_speech and speaking:
            state.set_idle()
        if speaking and is_speech:
            interrupt_mgr.trigger()
        speaking = is_speech


async def stt_pipeline(frame_generator: asyncio.Queue, partial_q: asyncio.Queue, final_q: asyncio.Queue, vad_end_q: asyncio.Queue = None):
    # adapt frame queue to async generator consumed by STTService
    async def gen():
        while True:
            frame = await frame_generator.get()
            if frame is None:
                break
            yield frame

    stt = STTService(asyncio.get_event_loop(), partial_q, final_q, vad_end_q)
    await stt.transcribe_audio(gen())


async def speculative_manager(partial_q: asyncio.Queue, token_q: asyncio.Queue, interrupt_mgr: InterruptManager):
    """Launch speculative LLM requests on partial transcripts with debounce.

    Listens for partials from STT and starts a speculative LLM stream after a
    short debounce. If new partials arrive quickly the speculative task is
    restarted. On interrupt the speculative task is cancelled.
es of silence before end of utterance
    
    while True:
        frame
        await vad_event_queue.put(is_speech)
        # simple barge-in detection: if speaking and user starts speaking
        if speaking and is_speech:
            interrupt_mgr.trigger()
        speaking = is_speech SILENCE_THRESHOLD:
                # End of utterance detected - signal STT to flush
                if vad_end_queue:
                    try:
                        vad_end_queue.put_nowait(True)
                        print("VAD: end of utterance detected")
                    except Exception:
                        pass
                silence_count = 0
        else:
            silence_count = 0
            

    await stt.transcribe_audio(gen())


async def llm_and_tts_loop(final_q: asyncio.Queue, token_q: asyncio.Queue, playback_q: asyncio.Queue, interrupt_mgr: InterruptManager):: asyncio.Queue, token_q: asyncio.Queue, playback_q: asyncio.Queue, interrupt_mgr: InterruptManager, state: ConversationState, text_mode: bool = False):
    llm = LLMService(token_q)
    tts = TTSService(playback_q)
    state = ConversationState()

    async def sentence_stream():
        # naive sentence assembler from tokens
        buf = ""
        while True:
            tok = await token_q.get()
            if tok is None:
                break
            buf += tok
            # flush on punctuation
            if any(c in buf for c in '.!?'):
                # yield up to last punctuation
                idx = max(buf.rfind('.'), buf.rfind('!'), buf.rfind('?'))
                sentence = buf[:idx+1].strip()
                buf = buf[idx+1:]
                yield sentence
        # Flush any remaining buffer
        if buf.strip():
            yield buf.strip()

    # main loop waiting for final STT
    while True:
        user_text = await final_q.get()
        if user_text is None:
            break
        print(f"[LLM/TTS] Processing: '{user_text}'")
        state.set_thinking()
        
        # In text mode, don't use interrupt event - just wait for completion
        if text_mode:
            # Simple mode: just run LLM and TTS sequentially
            llm = LLMService(token_q)
            stop_event = asyncio.Event()
            llm_task = asyncio.create_task(llm.stream_response(user_text, stop_event))
            
            sent_gen = sentence_stream()
            tts_task = asyncio.create_task(tts.speak_sentences(sent_gen))
            
            # Wait for LLM to
        try:
            done
async def main_loop():
    loop = asyncio.get_event_loop()
    # queues between modules
    raw_audio_q = asyncio.Queue()
    frame_q = asyncio.Queue() tasks
            if i, tts_task],nterrupt_mgr.get_eventresurn(when=:yncio.FIRST_COMPLETED                fo
                    task.can        if intcrru)_mgr.g  _event(). s_set():
                    f r t  k in p nding  s          tate.set_int etask.cancsl(
            

 epr state.set_interrupted()
                else:te    rruptM          if tts_taskainnpendagg:
                        await es
t skau     dio_in.s       tart()

 paakdio_out = Audioyqdt =cep aExceniion as e:
                print(f"[LLM/TTS] Error: {e}")
        
        # Reset for next round
        interrupt_mgr.clear()
        state.set_listening()
        print("[LLM/TTS] Cycle complete, ready for next input")


async def main_loop(initial_text: str | None = None):
    loop = asyncio.get_event_loop()
    # queues between modules
    raw_audio_q = asyncio.Queue()
    frame_q = asyncio.Queue()
    vad_q = asyncio.Queue()
    vad_end_q = asyncio.Queue()  # Queue for end-of-utterance signals
    stt_partial_q = asyncio.Queue()
    stt_final_q = asyncio.Queue()
    llm_token_q = asyncio.Queue()
    playback_q = asyncio.Queue()

    interrupt_mgr = InterruptManager()
    state = ConversationState()

    # Only start audio if NOT in text-only mode
    audio_in = None
    if not initial_text:
        audio_in = Audio

    audio_out = AudioOutput(loop, playback_q)
    audio_out_task = asyncio.create_task(audio_out.play_loop())
eate_task(audio_out.play_loop())

    # background tasks pipeline with audio
    tasks = [
        asyncio.create_task(audio_producer(raw_audio_q, frame_q)),
        asyncio.create_task(vad_c, interrupt_mgr)),onsumerameasync,o.create_task(llm_a d_vts_loopastt_finql_q, llm_to er_q,u_gayback_q, r)t)rrup_mgr,    as)c,
    ]io.creprint("Background pipeline tasks started")(vad_consumer(frame_q, vad_q, interrupt
    t       asy_cao.sreate_tksk(st(_pipslin_(lname_q,eftt_paatial_q,mett_final_q, vad_end_q)),tt_par, stt_fiasy_cio.creaqe_task)spcul
t ve_manager( at_partial_q, llm_toksy_q, ncterrupt_mir)),
           oasyncic.creatl_tlsm(llm_aad_tts_lonp(stt_final_qs_loop(stt_final_q, ll asyncio.create_task(vad_consumer(frame_q_vad, vad_q, interrupt_mgr, state, vad_end_q)),m_        tokeasyncio.create_task(stt_pipn_ine(frame_q_stt, qtt_partial_q, stt_final_q, vad_end_q)),playback_q    asyncio.create_task(speculative_manager(stt_partial_q, llm_token_q, interrupt_mgr)),
            asyncio.create_task(llm_and_tts_loop(stt_final_q, llm_token_q, playback_q, interrupt_mgr, state)),
        ]
    else:
        , interrupt_mg, state)),r)),
    ]T, just go straight to LLM/TTS
        print("[Text-mode] Skipping audio input, using provided text directly")
        tasks = [
            asyncio.create_task(llm_and_tts_loop(stt_final_q, llm_token_q, playback_q, interrupt_mgr, state, text_mode=True)),
        ]
    print("Background pipeline tasks started")
    print(f"Tasks: {len(tasks)}")
    # indicate ready for user speech
    try:
        print("Ready — Listening for input. Speak now.")
        state.set_listening()
    except Exception:
        pass

    # simple monitor printing partial STT and LLM tokens
     partial = await asyncio.wait_for(stt_partial_q.get(), timeout=1.0)async def monitor():
        while True:
            try:
                # Use wait_for to avoid blocking forev            except asyncio.   break
        trypar        tial stt]", print(f"[monitor]pqueueasizes:rframe={frame_q.qsize()}tpartials={stt_iartial_q.qlize()} token)={llm_token_q
            # forward partials optionally to LLM speculative agent (phase 2)

    mon = asyncio.create_task(monitor())

    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        pass
    finally:
        if audio_in:
            audio_in.stop()
        audio_out.shutdown()
        await playback_q.put(None)
        await mon


if __name__ == "__main__":
    asyncio.run(main_loop())
