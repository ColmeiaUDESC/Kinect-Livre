#ifndef PANELPREVIEW_INCLUDED
#define PANELPREVIEW_INCLUDED

#include <stdio.h>
#include <string>
#include <vector>
#include <GL/gl.h>
#include <GL/Extensions/GLEXTFramebufferObject.h>
#include <GL/Extensions/GLEXTFramebufferBlit.h>

/* Copies an already-rendered frame; never captures the Kinect or simulates water again. */
class PanelPreview
{
private:
    GLuint framebuffer,texture;
    double start,lastImage,fps;
    unsigned int frames;
    bool supported;
    std::vector<unsigned char> pixels;
public:
    PanelPreview():framebuffer(0),texture(0),start(-1.0),lastImage(-1.0),fps(0.0),frames(0),
        supported(GLEXTFramebufferBlit::isSupported())
    {
        if(supported) GLEXTFramebufferBlit::initExtension();
    }
    ~PanelPreview()
    {
        if(framebuffer) glDeleteFramebuffersEXT(1,&framebuffer);
        if(texture) glDeleteTextures(1,&texture);
    }
    void update(const std::string& path,double now,const GLint* viewport,double rate)
    {
        if(start<0.0) start=now;
        else ++frames;
        if(now-start>=1.0)
        {
            fps=double(frames)/(now-start);
            frames=0;
            start=now;
            std::string target=path+".json",temporary=target+".tmp";
            FILE* out=fopen(temporary.c_str(),"w");
            if(out)
            {
                fprintf(out,"{\"fps\":%.2f,\"preview_supported\":%s}\n",fps,supported?"true":"false");
                bool ok=fclose(out)==0;
                if(ok) rename(temporary.c_str(),target.c_str());
            }
        }
        if(!supported||rate<=0.0||viewport[2]<=0||viewport[3]<=0) return;
        double actualRate=fps>0.0&&fps<15.0?1.0:rate;
        if(lastImage>=0.0&&now-lastImage<1.0/actualRate) return;
        lastImage=now;
        int width=320,height=int(320.0*viewport[3]/viewport[2]+0.5);
        if(height>240) {height=240; width=int(240.0*viewport[2]/viewport[3]+0.5);}
        if(width<1||height<1) return;
        GLint oldRead,oldDraw;
        glGetIntegerv(GL_READ_FRAMEBUFFER_BINDING_EXT,&oldRead);
        glGetIntegerv(GL_DRAW_FRAMEBUFFER_BINDING_EXT,&oldDraw);
        glPushAttrib(GL_COLOR_BUFFER_BIT|GL_PIXEL_MODE_BIT|GL_TEXTURE_BIT|GL_ENABLE_BIT);
        glPushClientAttrib(GL_CLIENT_PIXEL_STORE_BIT);
        glDisable(GL_SCISSOR_TEST);
        if(!framebuffer)
        {
            glGenFramebuffersEXT(1,&framebuffer);
            glGenTextures(1,&texture);
            glBindTexture(GL_TEXTURE_2D,texture);
            glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_LINEAR);
            glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_LINEAR);
            glTexImage2D(GL_TEXTURE_2D,0,GL_RGB8,320,240,0,GL_RGB,GL_UNSIGNED_BYTE,0);
            glBindFramebufferEXT(GL_DRAW_FRAMEBUFFER_EXT,framebuffer);
            glFramebufferTexture2DEXT(GL_DRAW_FRAMEBUFFER_EXT,GL_COLOR_ATTACHMENT0_EXT,GL_TEXTURE_2D,texture,0);
            supported=glCheckFramebufferStatusEXT(GL_DRAW_FRAMEBUFFER_EXT)==GL_FRAMEBUFFER_COMPLETE_EXT;
        }
        bool copied=false;
        if(supported)
        {
            glBindFramebufferEXT(GL_READ_FRAMEBUFFER_EXT,oldDraw);
            glReadBuffer(oldDraw==0?GL_BACK:GL_COLOR_ATTACHMENT0_EXT);
            glBindFramebufferEXT(GL_DRAW_FRAMEBUFFER_EXT,framebuffer);
            glDrawBuffer(GL_COLOR_ATTACHMENT0_EXT);
            glBlitFramebufferEXT(viewport[0],viewport[1],viewport[0]+viewport[2],viewport[1]+viewport[3],
                                 0,0,width,height,GL_COLOR_BUFFER_BIT,GL_LINEAR);
            glBindFramebufferEXT(GL_READ_FRAMEBUFFER_EXT,framebuffer);
            glReadBuffer(GL_COLOR_ATTACHMENT0_EXT);
            glPixelStorei(GL_PACK_ALIGNMENT,1);
            glPixelStorei(GL_PACK_ROW_LENGTH,0);
            glPixelStorei(GL_PACK_SKIP_ROWS,0);
            glPixelStorei(GL_PACK_SKIP_PIXELS,0);
            pixels.resize(width*height*3);
            glReadPixels(0,0,width,height,GL_RGB,GL_UNSIGNED_BYTE,&pixels[0]);
            copied=true;
        }
        glBindFramebufferEXT(GL_READ_FRAMEBUFFER_EXT,oldRead);
        glBindFramebufferEXT(GL_DRAW_FRAMEBUFFER_EXT,oldDraw);
        glPopClientAttrib();
        glPopAttrib();
        if(copied)
        {
            std::string temporary=path+".tmp";
            FILE* out=fopen(temporary.c_str(),"wb");
            if(out)
            {
                bool ok=fprintf(out,"P6\n%d %d\n255\n",width,height)>0;
                for(int y=height-1;y>=0;--y)
                    ok=(fwrite(&pixels[y*width*3],1,width*3,out)==size_t(width*3))&&ok;
                ok=(fclose(out)==0)&&ok;
                if(ok) rename(temporary.c_str(),path.c_str());
            }
        }
    }
};
#endif
