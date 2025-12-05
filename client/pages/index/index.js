const app = getApp()

Page({
    data: {
        roomId: '',
        joinRoomId: '',
        password: ''
    },

    onLoad() {
    },

    onInput(e) {
        this.setData({
            roomId: e.detail.value
        })
    },

    onJoinInput(e) {
        this.setData({
            joinRoomId: e.detail.value
        })
    },

    onPasswordInput(e) {
        this.setData({
            password: e.detail.value
        })
    },

    createRoom() {
        if (!this.data.roomId) {
            wx.showToast({
                title: '请输入房间号',
                icon: 'none'
            })
            return
        }
        wx.navigateTo({
            url: `/pages/chat/chat?roomId=${this.data.roomId}&password=${this.data.password}&action=create`
        })
    },

    joinRoom() {
        if (!this.data.joinRoomId) {
            wx.showToast({
                title: '请输入房间号',
                icon: 'none'
            })
            return
        }
        wx.navigateTo({
            url: `/pages/chat/chat?roomId=${this.data.joinRoomId}&action=join`
        })
    }
})
