const app = getApp()

Page({
    data: {
        roomId: '',
        messages: [],
        inputValue: '',
        socketOpen: false,
        userInfo: {},
        hasUserInfo: false,
        userId: '',
        scrollTop: 0
    },

    onLoad(options) {
        this.setData({
            roomId: options.roomId
        })

        wx.setNavigationBarTitle({
            title: `Room: ${options.roomId}`
        })

        // Check for existing userId or generate new one
        let userId = wx.getStorageSync('userId')
        if (!userId) {
            userId = this.generateUserId()
            wx.setStorageSync('userId', userId)
        }
        this.setData({ userId })

        // Check for cached userInfo
        const userInfo = wx.getStorageSync('userInfo')
        if (userInfo) {
            this.setData({
                userInfo: userInfo,
                hasUserInfo: true
            })
            this.connectSocket()
        }
    },

    onUnload() {
        if (this.data.socketOpen) {
            wx.closeSocket()
        }
    },

    generateUserId() {
        return 'user_' + Math.random().toString(36).substr(2, 9);
    },

    onChooseAvatar(e) {
        const { avatarUrl } = e.detail
        this.setData({
            tempAvatarUrl: avatarUrl
        })
    },

    onNicknameChange(e) {
        this.setData({
            tempNickname: e.detail.value
        })
    },

    submitLogin() {
        if (!this.data.tempAvatarUrl || !this.data.tempNickname) {
            wx.showToast({
                title: 'Please set avatar and nickname',
                icon: 'none'
            })
            return
        }

        const fs = wx.getFileSystemManager()

        // Read the avatar file and convert to Base64
        fs.readFile({
            filePath: this.data.tempAvatarUrl,
            encoding: 'base64',
            success: (res) => {
                const base64Avatar = 'data:image/png;base64,' + res.data

                const userInfo = {
                    avatarUrl: base64Avatar,
                    nickName: this.data.tempNickname
                }

                // Cache user info
                wx.setStorageSync('userInfo', userInfo)

                this.setData({
                    userInfo: userInfo,
                    hasUserInfo: true
                })
                this.connectSocket()
            },
            fail: (err) => {
                console.error('Failed to read avatar', err)
                wx.showToast({
                    title: 'Avatar processing failed',
                    icon: 'none'
                })
            }
        })
    },

    connectSocket() {
        const that = this
        // Replace with your local IP if testing on device
        const url = 'wss://abc.tongchengxuanshang.com'
        // const url = 'ws://172.16.0.103:8090'

        wx.connectSocket({
            url: url
        })

        wx.onSocketOpen(() => {
            console.log('WebSocket Connected')
            that.setData({ socketOpen: true })

            // Join room with user info
            const joinPayload = {
                roomId: that.data.roomId,
                userInfo: {
                    ...that.data.userInfo,
                    userId: that.data.userId
                }
            }

            that.send({
                type: 'join',
                payload: joinPayload
            })
        })

        wx.onSocketMessage((res) => {
            try {
                const data = JSON.parse(res.data)
                console.log('Received:', data)

                if (data.type === 'history') {
                    const historyMessages = data.payload
                    that.setData({
                        messages: historyMessages,
                        scrollTop: historyMessages.length * 1000
                    })
                } else if (data.type === 'message' || data.type === 'system') {
                    const messages = that.data.messages
                    messages.push(data.payload)
                    that.setData({
                        messages: messages,
                        scrollTop: messages.length * 1000 // Auto scroll to bottom
                    })
                }
            } catch (e) {
                console.error(e)
            }
        })

        wx.onSocketClose(() => {
            console.log('WebSocket Closed')
            that.setData({ socketOpen: false })
        })

        wx.onSocketError((err) => {
            console.error('WebSocket Error', err)
        })
    },

    onInput(e) {
        this.setData({
            inputValue: e.detail.value
        })
    },

    sendMessage() {
        if (!this.data.inputValue || !this.data.socketOpen) return

        this.send({
            type: 'message',
            payload: { text: this.data.inputValue }
        })

        this.setData({
            inputValue: ''
        })
    },

    send(data) {
        if (this.data.socketOpen) {
            wx.sendSocketMessage({
                data: JSON.stringify(data)
            })
        }
    }
})
