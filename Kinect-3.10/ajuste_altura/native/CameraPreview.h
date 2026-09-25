// Reduced RGB or raw depth preview for the control panel; never drawn on the projector.
#ifndef CAMERA_PREVIEW_INCLUDED
#define CAMERA_PREVIEW_INCLUDED
#include <algorithm>
#include <cstdio>
#include <string>
#include <vector>
#include <Kinect/FrameBuffer.h>
#include <Kinect/FrameSource.h>

inline bool writeCameraPreview(const std::string& path,const Kinect::FrameBuffer& frame,bool depth=false)
{
    if(!frame.isValid()||frame.getSize(0)<=0||frame.getSize(1)<=0) return false;
    const int sw=frame.getSize(0),sh=frame.getSize(1);
    const double scale=std::min(1.0,std::min(320.0/sw,240.0/sh));
    const int width=std::max(1,int(sw*scale)),height=std::max(1,int(sh*scale));
    const unsigned char* source=frame.getData<unsigned char>();
    const Kinect::FrameSource::DepthPixel* depths=frame.getData<Kinect::FrameSource::DepthPixel>();
    int low=0,high=Kinect::FrameSource::invalidDepth-1;
    if(depth)
    {
        // Robust contrast from actual depth samples; black is reserved for holes.
        std::vector<unsigned int> histogram(Kinect::FrameSource::invalidDepth,0);
        unsigned int count=0;
        for(int y=0;y<height;++y)
            for(int x=0;x<width;++x)
            {
                const unsigned int d=depths[(y*sh/height)*sw+x*sw/width];
                if(d<Kinect::FrameSource::invalidDepth) {++histogram[d];++count;}
            }
        unsigned int cumulative=0;
        bool foundLow=false;
        for(int d=0;d<int(histogram.size())&&count;++d)
        {
            cumulative+=histogram[d];
            if(!foundLow&&cumulative>count/50) {low=d;foundLow=true;}
            if(cumulative>=count-count/50) {high=d;break;}
        }
        high=std::max(high,low+1);
    }
    std::vector<unsigned char> pixels(width*height*3);
    // Kinect frames start at the bottom; PPM starts at the top. No mirroring.
    for(int y=0;y<height;++y)
        for(int x=0;x<width;++x)
        {
            const int offset=((sh-1-y*sh/height)*sw+x*sw/width)*3;
            if(depth)
            {
                const unsigned int d=depths[offset/3];
                const unsigned char value=d>=Kinect::FrameSource::invalidDepth?0:
                    255-223*std::max(0,std::min(high-low,int(d)-low))/(high-low);
                for(int c=0;c<3;++c) pixels[(y*width+x)*3+c]=value;
            }
            else
                for(int c=0;c<3;++c) pixels[(y*width+x)*3+c]=source[offset+c];
        }
    const std::string temporary=path+".tmp";
    FILE* file=std::fopen(temporary.c_str(),"wb");
    if(!file) return false;
    bool ok=std::fprintf(file,"P6\n%d %d\n255\n",width,height)>0;
    ok=(std::fwrite(&pixels[0],1,pixels.size(),file)==pixels.size())&&ok;
    if(std::fclose(file)!=0) ok=false;
    if(ok) ok=std::rename(temporary.c_str(),path.c_str())==0;
    if(!ok) std::remove(temporary.c_str());
    return ok;
}
#endif
