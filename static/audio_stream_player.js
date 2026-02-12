/**
 * AudioStreamPlayer - Progressive audio playback for streaming TTS
 * Handles both audio URLs and raw audio data chunks
 */
class AudioStreamPlayer {
    constructor() {
        this.audioContext = null;
        this.audioQueue = [];
        this.isPlaying = false;
        this.currentSource = null;
        this.startTime = 0;
        this.nextStartTime = 0;
        this.onEndCallback = null;
    }

    async init() {
        if (!this.audioContext) {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
        }

        // Resume context if suspended (required by some browsers)
        if (this.audioContext.state === 'suspended') {
            await this.audioContext.resume();
        }
    }

    reset() {
        console.log('[AudioPlayer] ===== RESET CALLED =====');
        console.log('[AudioPlayer] Stopping current playback');
        console.log('[AudioPlayer] Clearing queue (current size:', this.audioQueue.length, ')');
        this.stop();
        this.audioQueue = [];
        this.nextStartTime = 0;
        console.log('[AudioPlayer] Reset complete');
    }

    stop() {
        console.log('[AudioStreamPlayer] Stopping playback');
        this.isPlaying = false;

        if (this.currentSource) {
            try {
                this.currentSource.stop();
            } catch (e) {
                // Already stopped
            }
            this.currentSource = null;
        }

        // Stop all queued audio
        this.audioQueue.forEach(item => {
            if (item.source) {
                try {
                    item.source.stop();
                } catch (e) {
                    // Already stopped
                }
            }
        });

        this.audioQueue = [];
    }

    async addAudioUrl(audioUrl) {
        console.log('[AudioPlayer] ----- ADD AUDIO URL -----');
        console.log('[AudioPlayer] URL:', audioUrl.substring(0, 80) + '...');
        console.log('[AudioPlayer] Current queue size:', this.audioQueue.length);
        console.log('[AudioPlayer] Is playing:', this.isPlaying);

        try {
            await this.init();

            console.log('[AudioPlayer] Fetching audio from URL...');
            // Fetch audio data
            const response = await fetch(audioUrl);
            const arrayBuffer = await response.arrayBuffer();
            console.log('[AudioPlayer] Fetched', arrayBuffer.byteLength, 'bytes');

            console.log('[AudioPlayer] Decoding audio data...');
            // Decode audio data
            const audioBuffer = await this.audioContext.decodeAudioData(arrayBuffer);
            console.log('[AudioPlayer] Decoded successfully');
            console.log('[AudioPlayer] Duration:', audioBuffer.duration.toFixed(2), 'seconds');
            console.log('[AudioPlayer] Sample rate:', audioBuffer.sampleRate, 'Hz');
            console.log('[AudioPlayer] Channels:', audioBuffer.numberOfChannels);

            // Add to queue
            this.audioQueue.push({
                type: 'buffer',
                buffer: audioBuffer,
                addedAt: new Date().toISOString()
            });

            console.log('[AudioPlayer] Added to queue. New queue size:', this.audioQueue.length);

            // Start playing if not already
            if (!this.isPlaying) {
                console.log('[AudioPlayer] Not currently playing, starting playback...');
                this.playNext();
            } else {
                console.log('[AudioPlayer] Already playing, chunk will play when ready');
            }

        } catch (error) {
            console.error('[AudioPlayer] ❌ Error adding audio URL:', error);
            throw error;
        }
    }

    async addAudioData(base64Data) {
        console.log('[AudioStreamPlayer] Adding raw audio data to queue');

        try {
            await this.init();

            // Decode base64 to ArrayBuffer
            const binaryString = window.atob(base64Data);
            const bytes = new Uint8Array(binaryString.length);
            for (let i = 0; i < binaryString.length; i++) {
                bytes[i] = binaryString.charCodeAt(i);
            }
            const arrayBuffer = bytes.buffer;

            // Decode audio data
            const audioBuffer = await this.audioContext.decodeAudioData(arrayBuffer);

            // Add to queue
            this.audioQueue.push({
                type: 'buffer',
                buffer: audioBuffer
            });

            console.log(`[AudioStreamPlayer] Audio data added (${audioBuffer.duration.toFixed(2)}s), queue size: ${this.audioQueue.length}`);

            // Start playing if not already
            if (!this.isPlaying) {
                this.playNext();
            }

        } catch (error) {
            console.error('[AudioStreamPlayer] Error adding audio data:', error);
            throw error;
        }
    }

    playNext() {
        if (this.audioQueue.length === 0) {
            console.log('[AudioPlayer] ===== QUEUE EMPTY =====');
            console.log('[AudioPlayer] All audio chunks have been played');
            console.log('[AudioPlayer] Playback complete');
            this.isPlaying = false;

            // Trigger end callback
            if (this.onEndCallback) {
                console.log('[AudioPlayer] Triggering onEnd callback');
                this.onEndCallback();
            }

            return;
        }

        this.isPlaying = true;

        const item = this.audioQueue.shift();
        const buffer = item.buffer;

        console.log('[AudioPlayer] ===== PLAYING NEXT CHUNK =====');
        console.log('[AudioPlayer] Duration:', buffer.duration.toFixed(2), 'seconds');
        console.log('[AudioPlayer] Remaining in queue:', this.audioQueue.length);
        console.log('[AudioPlayer] Added at:', item.addedAt);
        console.log('[AudioPlayer] Playing at:', new Date().toISOString());

        // Create buffer source
        const source = this.audioContext.createBufferSource();
        source.buffer = buffer;
        source.connect(this.audioContext.destination);

        // Schedule playback
        const currentTime = this.audioContext.currentTime;
        const startTime = Math.max(currentTime, this.nextStartTime);

        console.log('[AudioPlayer] AudioContext current time:', currentTime.toFixed(2), 's');
        console.log('[AudioPlayer] Scheduled start time:', startTime.toFixed(2), 's');
        console.log('[AudioPlayer] Next start time will be:', (startTime + buffer.duration).toFixed(2), 's');

        source.onended = () => {
            console.log('[AudioPlayer] ----- Chunk playback ended -----');
            console.log('[AudioPlayer] Moving to next chunk...');
            this.playNext();
        };

        source.start(startTime);
        this.currentSource = source;

        // Update next start time for seamless playback
        this.nextStartTime = startTime + buffer.duration;

        console.log('[AudioPlayer] Chunk started successfully');
    }

    setOnEndCallback(callback) {
        this.onEndCallback = callback;
    }
}

// Make available globally
window.AudioStreamPlayer = AudioStreamPlayer;
