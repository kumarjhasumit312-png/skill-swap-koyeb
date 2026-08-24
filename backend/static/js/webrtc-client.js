let localStream = null;
let peerConnection = null;
let socket = null;
let remoteUserPresent = false;

const rtcConfig = {
    iceServers: [
        { urls: "stun:stun.l.google.com:19302" },
        { urls: "stun:stun1.l.google.com:19302" }
    ]
};

document.addEventListener("DOMContentLoaded", async () => {
    const roomId = document.getElementById("roomId").value;
    const userId = document.getElementById("userId").value;
    const userName = document.getElementById("userName").value;

    const localVideo = document.getElementById("localVideo");
    const remoteVideo = document.getElementById("remoteVideo");
    const status = document.getElementById("meetingStatus");

    const audioButton = document.getElementById("toggleAudio");
    const videoButton = document.getElementById("toggleVideo");
    const screenButton = document.getElementById("shareScreen");
    const endButton = document.getElementById("endCall");

    const chatInput = document.getElementById("chatInput");
    const sendChatButton = document.getElementById("sendChat");
    const chatMessages = document.getElementById("chatMessages");

    function setStatus(message) {
        status.textContent = message;
        console.log(message);
    }

    function addChatMessage(name, message) {
        const item = document.createElement("div");
        item.textContent = `${name}: ${message}`;
        chatMessages.appendChild(item);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    try {
        localStream = await navigator.mediaDevices.getUserMedia({
            video: true,
            audio: true
        });

        localVideo.srcObject = localStream;
        await localVideo.play().catch(() => {});
        setStatus("Camera ready. Waiting for partner...");
    } catch (error) {
        console.error(error);
        setStatus("Camera/microphone error: " + error.message);
        alert("Camera and microphone permission allow karo.");
        return;
    }

    socket = io();

    socket.on("connect", () => {
        console.log("Socket connected:", socket.id);

        socket.emit("join-meeting", {
            roomId: roomId,
            userId: userId,
            userName: userName
        });
    });

    socket.on("user-joined", async (data) => {
        if (data.userId === userId) return;

        remoteUserPresent = true;
        document.getElementById("remoteName").textContent =
            data.userName || "Partner";

        setStatus("Partner joined. Connecting video...");

        await createOffer(roomId, userId);
    });

    socket.on("webrtc-offer", async (data) => {
        if (data.fromUserId === userId) return;

        remoteUserPresent = true;
        setStatus("Receiving partner video...");

        await createPeerConnection(roomId, userId);

        await peerConnection.setRemoteDescription(
            new RTCSessionDescription(data.offer)
        );

        const answer = await peerConnection.createAnswer();

        await peerConnection.setLocalDescription(answer);

        socket.emit("webrtc-answer", {
            roomId: roomId,
            fromUserId: userId,
            answer: peerConnection.localDescription
        });
    });

    socket.on("webrtc-answer", async (data) => {
        if (data.fromUserId === userId || !peerConnection) return;

        await peerConnection.setRemoteDescription(
            new RTCSessionDescription(data.answer)
        );

        setStatus("Video connected.");
    });

    socket.on("webrtc-ice-candidate", async (data) => {
        if (
            data.fromUserId === userId ||
            !data.candidate ||
            !peerConnection
        ) {
            return;
        }

        try {
            await peerConnection.addIceCandidate(
                new RTCIceCandidate(data.candidate)
            );
        } catch (error) {
            console.error("ICE candidate error:", error);
        }
    });

    socket.on("chat-message", (data) => {
        addChatMessage(data.userName, data.message);
    });

    async function createPeerConnection(roomId, userId) {
        if (peerConnection) {
            peerConnection.close();
        }

        peerConnection = new RTCPeerConnection(rtcConfig);

        localStream.getTracks().forEach((track) => {
            peerConnection.addTrack(track, localStream);
        });

        peerConnection.ontrack = async (event) => {
            remoteVideo.srcObject = event.streams[0];
            await remoteVideo.play().catch(() => {});
            setStatus("Video connected.");
        };

        peerConnection.onicecandidate = (event) => {
            if (event.candidate) {
                socket.emit("webrtc-ice-candidate", {
                    roomId: roomId,
                    fromUserId: userId,
                    candidate: event.candidate
                });
            }
        };

        peerConnection.onconnectionstatechange = () => {
            const connectionState = peerConnection.connectionState;

            if (connectionState === "connected") {
                setStatus("Video connected.");
            }

            if (
                connectionState === "disconnected" ||
                connectionState === "failed" ||
                connectionState === "closed"
            ) {
                setStatus("Partner disconnected.");
            }
        };
    }

    async function createOffer(roomId, userId) {
        await createPeerConnection(roomId, userId);

        const offer = await peerConnection.createOffer();

        await peerConnection.setLocalDescription(offer);

        socket.emit("webrtc-offer", {
            roomId: roomId,
            fromUserId: userId,
            offer: peerConnection.localDescription
        });
    }

    audioButton.addEventListener("click", () => {
        const audioTrack = localStream.getAudioTracks()[0];

        if (!audioTrack) return;

        audioTrack.enabled = !audioTrack.enabled;

        audioButton.textContent = audioTrack.enabled
            ? "🎤 Audio"
            : "🔇 Muted";
    });

    videoButton.addEventListener("click", () => {
        const videoTrack = localStream.getVideoTracks()[0];

        if (!videoTrack) return;

        videoTrack.enabled = !videoTrack.enabled;

        videoButton.textContent = videoTrack.enabled
            ? "📹 Camera"
            : "📷 Camera Off";
    });

    screenButton.addEventListener("click", async () => {
        try {
            const screenStream = await navigator.mediaDevices.getDisplayMedia({
                video: true,
                audio: false
            });

            const screenTrack = screenStream.getVideoTracks()[0];

            localVideo.srcObject = screenStream;

            const sender = peerConnection
                ?.getSenders()
                .find((item) => item.track && item.track.kind === "video");

            if (sender) {
                await sender.replaceTrack(screenTrack);
            }

            screenButton.textContent = "🖥️ Sharing Screen";

            screenTrack.addEventListener("ended", async () => {
                const cameraTrack = localStream.getVideoTracks()[0];

                localVideo.srcObject = localStream;

                if (sender && cameraTrack) {
                    await sender.replaceTrack(cameraTrack);
                }

                screenButton.textContent = "🖥️ Share Screen";
            });
        } catch (error) {
            if (error.name !== "NotAllowedError") {
                console.error("Screen share error:", error);
                alert("Screen sharing failed: " + error.message);
            }
        }
    });

    endButton.addEventListener("click", () => {
        if (peerConnection) {
            peerConnection.close();
        }

        if (localStream) {
            localStream.getTracks().forEach((track) => track.stop());
        }

        if (socket) {
            socket.disconnect();
        }

        window.location.href = "/dashboard";
    });

    sendChatButton.addEventListener("click", sendChat);

    chatInput.addEventListener("keydown", (event) => {
        if (event.key === "Enter") {
            sendChat();
        }
    });

    function sendChat() {
        const message = chatInput.value.trim();

        if (!message) return;

        socket.emit("chat-message", {
            roomId: roomId,
            userName: userName,
            message: message
        });

        chatInput.value = "";
    }
});