const app = getApp()

Page({
    data: {
        roomId: ''
    },

    onLoad() {
    },

    onInput(e) {
        this.setData({
            roomId: e.detail.value
        })
    },

    createRoom() {
        const roomId = Math.floor(1000 + Math.random() * 9000).toString();
        wx.navigateTo({
            url: `/pages/chat/chat?roomId=${roomId}`
        })
    },

    joinRoom() {
        if (!this.data.roomId) {
            wx.showToast({
                title: 'Please enter Room ID',
                icon: 'none'
            })
            return
        }
        wx.navigateTo({
            url: `/pages/chat/chat?roomId=${this.data.roomId}`
        })
    }
})
